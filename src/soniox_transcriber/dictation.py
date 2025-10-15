#!/usr/bin/env python3
"""
System-wide dictation tool using Soniox
Types transcribed text into any focused application (Sublime Text, browsers, etc.)
"""
import json
import os
import threading
import queue
import sys
import time
from typing import Optional
from dotenv import load_dotenv

import pyaudio
import pyautogui
from pynput import keyboard
from websockets import ConnectionClosedOK
from websockets.sync.client import connect

# Load environment variables
load_dotenv()

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"

# Audio recording parameters
CHUNK_SIZE = 3840
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Global state
is_recording = False
recording_lock = threading.Lock()


def get_config(api_key: str) -> dict:
    """Configure Soniox STT settings for dictation."""
    config = {
        "api_key": api_key,
        "model": "stt-rt-preview",
        "audio_format": "pcm_s16le",
        "sample_rate": RATE,
        "num_channels": CHANNELS,
        "language_hints": ["en"],
        "enable_endpoint_detection": True,
    }
    return config


def capture_audio(audio_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Capture audio from microphone and put chunks into queue."""
    p = pyaudio.PyAudio()

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        while not stop_event.is_set():
            with recording_lock:
                if not is_recording:
                    time.sleep(0.1)
                    continue

            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_queue.put(data)
            except Exception as e:
                print(f"⚠️  Error reading audio: {e}")
                break

        stream.stop_stream()
        stream.close()

    except Exception as e:
        print(f"\n❌ Error initializing audio: {e}")
        print("\nTroubleshooting tips:")
        print("- Make sure your microphone is connected")
        print("- Check System Settings > Privacy & Security > Microphone")
        print("- Grant microphone permission to your terminal/Python")

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
            with recording_lock:
                if not is_recording:
                    time.sleep(0.1)
                    continue

            try:
                data = audio_queue.get(timeout=0.1)
                ws.send(data)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️  Error sending audio: {e}")
                break

    except Exception as e:
        print(f"⚠️  Error in audio streaming: {e}")


def normalize_text(text: str) -> str:
    """
    Normalize text for typing:
    - Remove <END> markers
    - Convert all uppercase to sentence case
    - Preserve proper spacing
    """
    # Remove <END> markers
    text = text.replace("<END>", "").replace("<end>", "")

    # Check if text is all uppercase (more than 70% uppercase letters)
    if text.strip():
        uppercase_count = sum(1 for c in text if c.isupper())
        letter_count = sum(1 for c in text if c.isalpha())

        if letter_count > 0 and uppercase_count / letter_count > 0.7:
            # Convert to sentence case: lowercase everything first
            text = text.lower()

            # Capitalize first letter of the text
            if text and text[0].isalpha():
                text = text[0].upper() + text[1:]

            # Capitalize after sentence-ending punctuation (., !, ?)
            import re
            def capitalize_after_punctuation(match):
                return match.group(0)[:-1] + match.group(0)[-1].upper()

            text = re.sub(r'[.!?]\s+([a-z])', capitalize_after_punctuation, text)

    return text


def type_text(text: str) -> None:
    """Type text into the currently focused application."""
    try:
        # Normalize the text before typing
        text = normalize_text(text)

        # Skip if text is empty after normalization
        if not text.strip():
            return

        # Small delay to ensure focus is maintained
        time.sleep(0.05)
        pyautogui.write(text, interval=0.01)
    except Exception as e:
        print(f"⚠️  Error typing text: {e}")


class DictationSession:
    """Manages a dictation session with Soniox."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.ws = None
        self.final_tokens = []
        self.last_typed_count = 0

    def start(self):
        """Start the dictation session."""
        config = get_config(self.api_key)

        try:
            self.ws = connect(SONIOX_WEBSOCKET_URL)
            self.ws.send(json.dumps(config))

            # Start audio capture thread
            self.capture_thread = threading.Thread(
                target=capture_audio,
                args=(self.audio_queue, self.stop_event),
                daemon=True,
            )
            self.capture_thread.start()

            # Start audio streaming thread
            self.streaming_thread = threading.Thread(
                target=stream_audio_to_websocket,
                args=(self.audio_queue, self.ws, self.stop_event),
                daemon=True,
            )
            self.streaming_thread.start()

            print("✅ Connected to Soniox!")

        except Exception as e:
            print(f"❌ Error connecting: {e}")
            raise

    def process_transcription(self):
        """Process incoming transcription and type text."""
        try:
            while not self.stop_event.is_set():
                try:
                    message = self.ws.recv(timeout=0.1)
                except TimeoutError:
                    continue

                res = json.loads(message)

                # Check for errors
                if res.get("error_code") is not None:
                    print(f"\n❌ Error: {res['error_code']} - {res['error_message']}")
                    break

                # Parse tokens
                for token in res.get("tokens", []):
                    if token.get("text") and token.get("is_final"):
                        self.final_tokens.append(token)

                # Type new final tokens
                if len(self.final_tokens) > self.last_typed_count:
                    new_tokens = self.final_tokens[self.last_typed_count:]
                    for token in new_tokens:
                        text = token["text"]
                        type_text(text)
                    self.last_typed_count = len(self.final_tokens)

                # Check if session finished
                if res.get("finished"):
                    break

        except ConnectionClosedOK:
            pass
        except Exception as e:
            print(f"⚠️  Error processing transcription: {e}")

    def stop(self):
        """Stop the dictation session."""
        self.stop_event.set()
        if self.ws:
            try:
                self.ws.close()
            except:
                pass


def on_press(key, session: DictationSession):
    """Handle key press events."""
    global is_recording

    try:
        # Check for Fn key press (use Right Command as toggle for now)
        # On Mac, we'll use Cmd+Shift+Space as the toggle
        if hasattr(key, 'name'):
            # This gets triggered for special keys
            pass

    except AttributeError:
        pass


def on_activate():
    """Called when hotkey is pressed."""
    global is_recording
    with recording_lock:
        is_recording = not is_recording
        if is_recording:
            print("\n🎤 Recording STARTED - speak now!")
        else:
            print("\n⏸️  Recording PAUSED")


def run_dictation(api_key: str):
    """Run the dictation app with hotkey control."""
    global is_recording

    print("\n" + "=" * 60)
    print("🎙️  SONIOX DICTATION MODE")
    print("=" * 60)
    print("\nConnecting to Soniox...")

    # Set up PyAutoGUI safety
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.01

    session = DictationSession(api_key)

    try:
        session.start()

        print("\n📝 Ready to dictate!")
        print("\nControls:")
        print("  • Press Cmd+Shift+Space to START/STOP recording")
        print("  • Press Ctrl+C to quit")
        print("\nWhen recording is active, your speech will be typed")
        print("into whatever application has focus.\n")
        print("-" * 60)

        # Set up global hotkey listener
        with keyboard.GlobalHotKeys({
            '<cmd>+<shift>+<space>': on_activate,
        }) as hotkey_listener:

            # Process transcription in main thread
            session.process_transcription()

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping dictation...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check your internet connection")
        print("- Verify SONIOX_API_KEY is correct")
        print("- Ensure you have API credits at console.soniox.com")
    finally:
        session.stop()
        print("\n" + "=" * 60)
        print("Goodbye!")
        print("=" * 60 + "\n")


def main():
    """Entry point for dictation mode."""
    api_key = os.environ.get("SONIOX_API_KEY")

    if api_key is None:
        print("\n❌ Error: SONIOX_API_KEY not found!")
        print("\nPlease set your API key:")
        print("1. Get your API key from https://console.soniox.com")
        print("2. Create a .env file with: SONIOX_API_KEY=your_key_here")
        print("   OR")
        print("   export SONIOX_API_KEY=your_key_here")
        sys.exit(1)

    # Check accessibility permissions
    print("\n⚠️  IMPORTANT: Accessibility Permissions Required")
    print("\nFor typing to work, you need to grant accessibility permissions:")
    print("1. Go to: System Settings > Privacy & Security > Accessibility")
    print("2. Enable access for your Terminal or Python")
    print("3. You may need to restart the app after granting permissions\n")

    input("Press Enter when ready to continue...")

    try:
        run_dictation(api_key)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
