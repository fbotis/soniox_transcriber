# Quick Start Guide - Soniox Dictation

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
brew install portaudio
uv sync
```

### 2. Set Up API Key
```bash
cp .env.example .env
# Edit .env and add your API key from console.soniox.com
```

### 3. Run Dictation Mode
```bash
uv run soniox-dictate
```

## 🎤 How to Use

1. **Start the app**: `uv run soniox-dictate`
2. **Grant permissions** when prompted (Microphone & Accessibility)
3. **Open any app** where you want to type (Sublime Text, Chrome, Notes, etc.)
4. **Press Cmd+Shift+Space** to start recording
5. **Speak naturally** - your words will be typed!
6. **Press Cmd+Shift+Space** again to pause
7. **Press Ctrl+C** in terminal to quit

## ⚙️ Required macOS Permissions

### Microphone Access
**System Settings > Privacy & Security > Microphone**
- Enable for Terminal (or iTerm, your terminal app)

### Accessibility (for typing)
**System Settings > Privacy & Security > Accessibility**
- Enable for Terminal (or iTerm, your terminal app)
- This allows the app to simulate keyboard input

**⚠️ Important:** Restart the app after granting permissions!

## 💡 Pro Tips

- **Punctuation**: Say "period", "comma", "question mark", "exclamation point"
- **New lines**: Say "new line" or "new paragraph"
- **Best results**:
  - Speak clearly and at normal pace
  - Use a good microphone (built-in Mac mic works fine)
  - Minimize background noise
  - Click into a text field before speaking

## 🎯 Example Workflow

```bash
# Terminal 1: Start dictation
uv run soniox-dictate

# 1. App shows: "Press Cmd+Shift+Space to START/STOP recording"
# 2. Open Sublime Text, create new file
# 3. Press Cmd+Shift+Space (terminal shows: "🎤 Recording STARTED")
# 4. Speak: "Hello world, this is a test of the dictation system."
# 5. Watch the text appear in Sublime Text!
# 6. Press Cmd+Shift+Space to pause
# 7. Continue editing, or speak more
```

## 🐛 Troubleshooting

### "Error initializing audio"
- Install PortAudio: `brew install portaudio`
- Check microphone in System Settings

### "SONIOX_API_KEY not found"
- Create `.env` file with your API key
- Get key from: https://console.soniox.com

### Text not appearing when I speak
- Grant Accessibility permissions in System Settings
- Make sure recording is ON (see "🎤 Recording STARTED")
- Click into a text field in your target app
- Restart the app after granting permissions

### Hotkey not working
- Make sure app is running (check terminal)
- Try pressing Cmd+Shift+Space again
- Check for conflicts with other apps using same hotkey

## 📚 More Info

See [README.md](README.md) for detailed documentation.
