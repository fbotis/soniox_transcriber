# Soniox Live Transcriber for Mac

A real-time speech-to-text application that captures audio from your microphone and transcribes it live using the Soniox API. **Now with system-wide dictation mode** - type anywhere by speaking!

## Features

- **🎤 System-wide dictation**: Speak and type into ANY application (Sublime Text, browsers, documents, etc.)
- **🔌 Vapi integration**: Use Soniox as a custom transcriber for Vapi voice AI applications
- **📝 Console transcription**: View transcription in terminal with speaker labels
- **🎯 Hotkey control**: Easy start/stop with Cmd+Shift+Space
- **🗣️ Speaker diarization**: Automatically identifies different speakers
- **🌍 Language detection**: Detects the language being spoken
- **⏱️ Endpoint detection**: Intelligently detects when user stops speaking
- **✨ High accuracy**: Powered by Soniox's state-of-the-art speech recognition

## Prerequisites

- Python 3.8 or higher
- macOS (tested on macOS)
- A working microphone
- Soniox API key (get one at [console.soniox.com](https://console.soniox.com))

## Installation

### 1. Install PortAudio (required for PyAudio)

```bash
brew install portaudio
```

### 2. Install Python dependencies

Using pip:
```bash
pip install -e .
```

Or using uv (faster):
```bash
uv sync
```

### 3. Set up your API key

Create a `.env` file in the project directory:
```bash
SONIOX_API_KEY=your_api_key_here
```

Or export it as an environment variable:
```bash
export SONIOX_API_KEY=your_api_key_here
```

## Usage

### 🎤 Dictation Mode (Recommended)

**Type anywhere by speaking!** Open any app (Sublime Text, browser, etc.) and use voice to type:

```bash
uv run soniox-dictate
```

**Controls:**
- **Cmd+Shift+Space**: Toggle recording ON/OFF
- Focus any application (Sublime Text, Chrome, etc.)
- Start speaking when recording is ON
- Your speech will be typed automatically!
- **Ctrl+C**: Quit the app

### 📝 Console Transcription Mode

View transcription in the terminal (doesn't type into apps):

```bash
uv run soniox-transcriber
```

**Controls:**
- **Start speaking**: Transcription appears in console
- **Ctrl+C**: Stop

### 🔌 Vapi Custom Transcriber Server

Use Soniox as a custom transcriber for your Vapi voice AI applications:

```bash
uv run soniox-vapi-server
```

**See [VAPI_INTEGRATION.md](VAPI_INTEGRATION.md) for complete setup guide**, including:
- How to expose your server with ngrok
- Configuring Vapi to use your transcriber
- Production deployment options
- Troubleshooting tips

## Required Permissions on macOS

### For Microphone Access:
1. Go to **System Settings > Privacy & Security > Microphone**
2. Enable access for your Terminal app or Python
3. Restart your terminal if needed

### For Dictation Mode (Typing):
1. Go to **System Settings > Privacy & Security > Accessibility**
2. Enable access for your Terminal app or Python
3. This allows the app to simulate keyboard input
4. Restart the app after granting permissions

## Troubleshooting

### "Error initializing audio"
- Make sure PortAudio is installed: `brew install portaudio`
- Check that your microphone is connected and working
- Verify microphone permissions in System Settings

### "SONIOX_API_KEY not found"
- Make sure you created a `.env` file with your API key
- Or export the key: `export SONIOX_API_KEY=your_key`
- Get your API key from [console.soniox.com](https://console.soniox.com)

### "Connection error" or timeout
- Check your internet connection
- Verify your API key is correct and has available credits
- Visit [console.soniox.com](https://console.soniox.com) to check your account status

### Poor audio quality
- Use a good quality microphone (built-in Mac mic works fine)
- Reduce background noise
- Speak clearly and at a normal pace
- Make sure you're not too far from the microphone

### Dictation not typing into apps
- Grant Accessibility permissions in System Settings
- Make sure the target app has focus when you speak
- Try clicking into a text field before speaking
- Check that recording is ON (press Cmd+Shift+Space)

## How It Works

### Dictation Mode:
1. **Audio Capture**: Captures microphone audio at 16kHz
2. **Streaming**: Sends audio to Soniox WebSocket API in real-time
3. **Transcription**: Soniox returns transcribed text tokens
4. **Auto-typing**: PyAutoGUI simulates keyboard input into the focused app
5. **Hotkey Control**: Pynput listens for Cmd+Shift+Space to toggle recording

### Console Mode:
1. **Audio Capture**: Captures microphone audio
2. **Streaming**: Sends to Soniox API
3. **Transcription**: Receives tokens with speaker/language info
4. **Display**: Shows formatted transcript in terminal

## Configuration

You can customize the transcription settings:

**For dictation mode**: Edit [src/soniox_transcriber/dictation.py](src/soniox_transcriber/dictation.py)
**For console mode**: Edit [src/soniox_transcriber/transcriber.py](src/soniox_transcriber/transcriber.py)

Options:
- `language_hints`: Add languages you expect to use (default: English)
- `enable_speaker_diarization`: Toggle speaker identification (console mode)
- `enable_language_identification`: Toggle language detection
- `enable_endpoint_detection`: Toggle automatic endpoint detection
- Hotkey: Change `'<cmd>+<shift>+<space>'` in dictation.py to customize

## API Documentation

For more details about Soniox API features, visit:
- [Soniox Documentation](https://soniox.com/docs)
- [Real-time Transcription](https://soniox.com/docs/stt/rt/real-time-transcription)
- [WebSocket API Reference](https://soniox.com/docs/stt/api-reference/websocket-api)

## License

This project is open source and available under the MIT License.
