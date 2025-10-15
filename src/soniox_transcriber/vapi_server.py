#!/usr/bin/env python3
"""
Vapi Custom Transcriber Server using Soniox
WebSocket server that receives audio from Vapi and sends back Soniox transcriptions
"""
import asyncio
import json
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from aiohttp import web
import websockets
from websockets.asyncio.client import connect as ws_connect

# Load environment variables
load_dotenv()

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"


class VapiTranscriberSession:
    """Manages a single Vapi transcription session."""

    def __init__(self, vapi_ws, api_key: str):
        self.vapi_ws = vapi_ws
        self.api_key = api_key
        self.soniox_ws: Optional[Any] = None
        self.audio_config: Optional[Dict] = None
        self.running = True

    def get_soniox_config(self) -> dict:
        """Build Soniox configuration based on Vapi audio settings."""
        config = {
            "api_key": self.api_key,
            "model": "stt-rt-preview",
            "audio_format": "pcm_s16le",
            "sample_rate": self.audio_config.get("sampleRate", 16000),
            "num_channels": self.audio_config.get("channels", 2),
            "language_hints": ["en", "ro"],  # English and Romanian
            "enable_endpoint_detection": True,
            "enable_language_identification": False,
            "enable_speaker_diarization": True,  # Enable speaker identification
        }
        return config

    async def connect_to_soniox(self):
        """Establish connection to Soniox WebSocket API."""
        try:
            self.soniox_ws = await ws_connect(SONIOX_WEBSOCKET_URL)
            config = self.get_soniox_config()
            await self.soniox_ws.send(json.dumps(config))
            print(f"✅ Connected to Soniox (sample_rate={config['sample_rate']}, channels={config['num_channels']})")

            # Start the response handler task NOW that we're connected
            self.soniox_task = asyncio.create_task(self.process_soniox_responses())

            return True
        except Exception as e:
            print(f"❌ Error connecting to Soniox: {e}")
            return False

    async def handle_vapi_message(self, message):
        """Process incoming message from Vapi."""
        # Handle text messages (JSON)
        if isinstance(message, str):
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "start":
                    # Vapi sends audio configuration
                    self.audio_config = {
                        "encoding": data.get("encoding", "linear16"),
                        "container": data.get("container", "raw"),
                        "sampleRate": data.get("sampleRate", 16000),
                        "channels": data.get("channels", 2),
                    }
                    print(f"📥 Received Vapi start message: {self.audio_config}")

                    # Connect to Soniox with the audio config
                    await self.connect_to_soniox()

                else:
                    print(f"⚠️  Unknown message type from Vapi: {msg_type}")

            except json.JSONDecodeError:
                print(f"⚠️  Invalid JSON from Vapi: {message}")

        # Handle binary messages (audio data)
        elif isinstance(message, bytes):
            # Debug: Log audio reception
            if not hasattr(self, '_audio_count'):
                self._audio_count = 0
            self._audio_count += 1

            if self._audio_count % 100 == 0:  # Log every 100 chunks
                print(f"🎵 Received {self._audio_count} audio chunks ({len(message)} bytes)")

            if self.soniox_ws:
                try:
                    # Forward audio to Soniox
                    await self.soniox_ws.send(message)
                except Exception as e:
                    print(f"⚠️  Error sending audio to Soniox: {e}")
            else:
                print("⚠️  Received audio but Soniox not connected yet")

    async def process_soniox_responses(self):
        """Read transcription results from Soniox and send to Vapi."""
        if not self.soniox_ws:
            return

        print("🎧 Started listening for Soniox responses...")

        try:
            async for message in self.soniox_ws:
                if not self.running:
                    break

                try:
                    res = json.loads(message)

                    # Debug: Log all Soniox responses
                    print(f"🔊 Soniox response: {res}")

                    # Check for errors from Soniox
                    if res.get("error_code"):
                        print(f"❌ Soniox error: {res['error_code']} - {res['error_message']}")
                        continue

                    # Extract final transcription tokens with speaker info
                    final_tokens = []
                    speaker_id = None
                    for token in res.get("tokens", []):
                        if token.get("is_final") and token.get("text"):
                            final_tokens.append(token["text"])
                            # Get speaker from token (Soniox diarization provides this)
                            if speaker_id is None and "speaker" in token:
                                speaker_id = token["speaker"]

                    # Send transcription to Vapi if we have final tokens
                    if final_tokens:
                        transcription = "".join(final_tokens)

                        # Remove <end> and <END> markers
                        transcription = transcription.replace("<end>", "").replace("<END>", "").strip()

                        # Skip if empty after cleanup
                        if not transcription:
                            continue

                        # Determine speaker channel using Soniox speaker diarization
                        # Soniox identifies speakers as S0, S1, S2, etc.
                        # We need to map:
                        # - First speaker (S0) is typically the one who speaks first
                        # - In Vapi calls, assistant usually speaks first with firstMessage
                        # - So S0 = assistant, S1 = customer
                        # But this can vary, so we'll use a heuristic:
                        # - Track which speaker spoke first
                        if not hasattr(self, '_first_speaker'):
                            self._first_speaker = speaker_id
                            # Assume first speaker is the assistant (Riley's firstMessage)
                            self._assistant_speaker = speaker_id
                            vapi_channel = "assistant"
                        else:
                            # If same as first speaker, it's assistant; otherwise customer
                            if speaker_id == self._assistant_speaker:
                                vapi_channel = "assistant"
                            else:
                                vapi_channel = "customer"

                        # Send to Vapi in the expected format
                        vapi_response = {
                            "type": "transcriber-response",
                            "transcription": transcription,
                            "channel": vapi_channel,
                        }

                        await self.vapi_ws.send_json(vapi_response)
                        print(f"📤 Sent to Vapi [{vapi_channel}] (speaker: {speaker_id}): {transcription}")

                    # Check if session finished
                    if res.get("finished"):
                        print("✅ Soniox session finished")
                        break

                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON from Soniox: {message}")
                except Exception as e:
                    print(f"⚠️  Error processing Soniox response: {e}")

        except Exception as e:
            print(f"⚠️  Error in Soniox response handler: {e}")

    async def close(self):
        """Clean up connections."""
        self.running = False
        if self.soniox_ws:
            try:
                await self.soniox_ws.close()
            except:
                pass


async def websocket_handler(request):
    """Handle incoming WebSocket connection from Vapi."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    print("\n" + "=" * 60)
    print("📞 New Vapi connection received")
    print("=" * 60)

    # Get API key from environment
    api_key = os.environ.get("SONIOX_API_KEY")
    if not api_key:
        await ws.send_json({
            "error": "SONIOX_API_KEY not configured on server"
        })
        await ws.close()
        return ws

    # Create transcription session
    session = VapiTranscriberSession(ws, api_key)

    try:
        # Process messages from Vapi
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await session.handle_vapi_message(msg.data)
            elif msg.type == web.WSMsgType.BINARY:
                await session.handle_vapi_message(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"⚠️  WebSocket error: {ws.exception()}")
                break
            elif msg.type == web.WSMsgType.CLOSE:
                print("📪 Vapi closed connection")
                break

        # Wait for Soniox handler to finish (if it was started)
        if hasattr(session, 'soniox_task'):
            await session.soniox_task

    except Exception as e:
        print(f"❌ Error in websocket handler: {e}")
    finally:
        await session.close()
        print("=" * 60)
        print("Session ended")
        print("=" * 60 + "\n")

    return ws


async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)


def create_app():
    """Create and configure the aiohttp application."""
    app = web.Application()

    # Add routes
    app.router.add_get("/api/custom-transcriber", websocket_handler)
    app.router.add_get("/health", health_check)

    return app


def main():
    """Run the Vapi custom transcriber server."""
    # Check for API key
    api_key = os.environ.get("SONIOX_API_KEY")
    if not api_key:
        print("\n❌ Error: SONIOX_API_KEY not found!")
        print("\nPlease set your API key:")
        print("1. Add to .env file: SONIOX_API_KEY=your_key_here")
        print("2. Or export: export SONIOX_API_KEY=your_key_here")
        print("\nGet your API key from: https://console.soniox.com")
        sys.exit(1)

    # Get configuration
    host = os.environ.get("VAPI_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("VAPI_SERVER_PORT", "8080"))

    print("\n" + "=" * 60)
    print("🚀 SONIOX VAPI CUSTOM TRANSCRIBER SERVER")
    print("=" * 60)
    print(f"\n📡 Server starting on {host}:{port}")
    print(f"🔗 WebSocket endpoint: ws://{host}:{port}/api/custom-transcriber")
    print(f"💚 Health check: http://{host}:{port}/health")
    print("\n📝 To use with Vapi:")
    print("   1. Expose this server with ngrok: ngrok http 8080")
    print("   2. Use the ngrok URL in your Vapi transcriber config")
    print("\n✅ Server ready - waiting for connections...")
    print("=" * 60 + "\n")

    # Create and run app
    app = create_app()
    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    main()
