#!/usr/bin/env python3
"""
Live Audio Transcriber for Mac using Soniox
Captures audio from your microphone and transcribes it in real-time.
"""
import json
import os
import threading
import queue
import sys
from typing import Optional
from dotenv import load_dotenv

import pyaudio
from websockets import ConnectionClosedOK
from websockets.sync.client import connect

# Load environment variables
load_dotenv()

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"

# Audio recording parameters
CHUNK_SIZE = 3840  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # Mono
RATE = 16000  # Sample rate (16kHz)


def get_config(api_key: str) -> dict:
    """Configure Soniox STT settings for live transcription."""
    config = {
        "api_key": api_key,
        "model": "stt-rt-preview",
        "audio_format": "pcm_s16le",
        "sample_rate": RATE,
        "num_channels": CHANNELS,
        "language_hints": ["en"],
        "enable_language_identification": True,
        "enable_endpoint_detection": True,
    }
    return config


def capture_audio(audio_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Capture audio from microphone and put chunks into queue."""
    p = pyaudio.PyAudio()

    try:
        # Open audio stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("🎤 Microphone active - start speaking...")

        while not stop_event.is_set():
            try:
                # Read audio data
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_queue.put(data)
            except Exception as e:
                print(f"Error reading audio: {e}")
                break

        # Clean up
        stream.stop_stream()
        stream.close()

    except Exception as e:
        print(f"Error initializing audio: {e}")
        print("\nTroubleshooting tips:")
        print("- Make sure your microphone is connected and working")
        print("- Check System Settings > Privacy & Security > Microphone")
        print("- You may need to grant microphone permission to your terminal/Python")

    finally:
        p.terminate()


def stream_audio_to_websocket(
    audio_queue: queue.Queue,
    ws,
    stop_event: threading.Event
) -> None:
    """Read audio chunks from queue and send to websocket."""
    try:
        while not stop_event.is_set():
            try:
                # Get audio data with timeout
                data = audio_queue.get(timeout=0.1)
                ws.send(data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error sending audio: {e}")
                break

        # Send end-of-audio signal
        ws.send("")

    except Exception as e:
        print(f"Error in audio streaming: {e}")


def render_tokens(final_tokens: list[dict], non_final_tokens: list[dict]) -> str:
    """Convert tokens into readable transcript."""
    text_parts: list[str] = []
    current_speaker: Optional[str] = None
    current_language: Optional[str] = None

    # Process all tokens in order
    for token in final_tokens + non_final_tokens:
        text = token["text"]
        speaker = token.get("speaker")
        language = token.get("language")

        # Speaker changed -> add a speaker tag
        if speaker is not None and speaker != current_speaker:
            if current_speaker is not None:
                text_parts.append("\n\n")
            current_speaker = speaker
            current_language = None
            text_parts.append(f"Speaker {current_speaker}:")

        # Language changed -> add a language tag
        if language is not None and language != current_language:
            current_language = language
            text_parts.append(f"\n[{current_language}] ")
            text = text.lstrip()

        text_parts.append(text)

    return "".join(text_parts)


def run_live_transcription(api_key: str) -> None:
    """Main function to run live transcription."""
    config = get_config(api_key)

    # Thread communication
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    print("\n" + "=" * 60)
    print("🎙️  SONIOX LIVE TRANSCRIBER")
    print("=" * 60)
    print("\nConnecting to Soniox...")

    try:
        with connect(SONIOX_WEBSOCKET_URL) as ws:
            # Send configuration
            ws.send(json.dumps(config))

            # Start audio capture thread
            capture_thread = threading.Thread(
                target=capture_audio,
                args=(audio_queue, stop_event),
                daemon=True,
            )
            capture_thread.start()

            # Start audio streaming thread
            streaming_thread = threading.Thread(
                target=stream_audio_to_websocket,
                args=(audio_queue, ws, stop_event),
                daemon=True,
            )
            streaming_thread.start()

            print("✅ Connected! Transcription will appear below:")
            print("-" * 60 + "\n")

            final_tokens: list[dict] = []

            try:
                while True:
                    # Receive transcription results
                    message = ws.recv()
                    res = json.loads(message)

                    # Check for errors
                    if res.get("error_code") is not None:
                        print(
                            f"\n❌ Error: {res['error_code']} - {res['error_message']}")
                        break

                    # Parse tokens
                    non_final_tokens: list[dict] = []
                    for token in res.get("tokens", []):
                        if token.get("text"):
                            if token.get("is_final"):
                                final_tokens.append(token)
                            else:
                                non_final_tokens.append(token)

                    # Clear previous line and render new transcript
                    if final_tokens or non_final_tokens:
                        # Move cursor up if we have non-final tokens to update
                        if non_final_tokens:
                            print("\r" + " " * 80 + "\r", end="")

                        # Render and print transcript
                        text = render_tokens(final_tokens, non_final_tokens)
                        if non_final_tokens:
                            # Print non-final tokens without newline
                            print(text, end="", flush=True)
                        else:
                            # Print final tokens with newline
                            print(text)

                    # Check if session finished
                    if res.get("finished"):
                        print("\n\n✅ Session finished.")
                        break

            except ConnectionClosedOK:
                print("\n\n✅ Connection closed.")

            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping transcription...")

            finally:
                # Stop threads
                stop_event.set()
                capture_thread.join(timeout=2)
                streaming_thread.join(timeout=2)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("- Check your internet connection")
        print("- Verify your SONIOX_API_KEY is correct")
        print("- Make sure you have API credits available at console.soniox.com")

    finally:
        print("\n" + "=" * 60)
        print("Goodbye!")
        print("=" * 60 + "\n")


def main():
    """Entry point for the live transcriber."""
    # Get API key from environment
    api_key = os.environ.get("SONIOX_API_KEY")

    if api_key is None:
        print("\n❌ Error: SONIOX_API_KEY not found!")
        print("\nPlease set your API key:")
        print("1. Get your API key from https://console.soniox.com")
        print("2. Create a .env file with: SONIOX_API_KEY=your_key_here")
        print("   OR")
        print("   export SONIOX_API_KEY=your_key_here")
        sys.exit(1)

    try:
        run_live_transcription(api_key)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
