# Vapi Integration - Soniox Custom Transcriber

This guide shows you how to use Soniox as a custom transcriber with Vapi for superior speech recognition in your voice AI applications.

## 🎯 What This Does

The Vapi custom transcriber server acts as a bridge between Vapi and Soniox:
- Receives audio from Vapi via WebSocket
- Forwards it to Soniox for real-time transcription
- Sends transcriptions back to Vapi
- Supports stereo audio and all Vapi audio configurations

## 📋 Prerequisites

- Python 3.8+
- Soniox API key from [console.soniox.com](https://console.soniox.com)
- Vapi account
- ngrok (for exposing local server to the internet)

## 🚀 Quick Start

### 1. Install ngrok

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up your API key

Make sure your `.env` file has your Soniox API key:
```bash
SONIOX_API_KEY=your_soniox_api_key_here
```

### 4. Start the Vapi transcriber server

```bash
uv run soniox-vapi-server
```

You should see:
```
🚀 SONIOX VAPI CUSTOM TRANSCRIBER SERVER
📡 Server starting on 0.0.0.0:8080
🔗 WebSocket endpoint: ws://0.0.0.0:8080/api/custom-transcriber
✅ Server ready - waiting for connections...
```

### 5. Expose server with ngrok

In a **new terminal**, run:
```bash
ngrok http 8080
```

ngrok will show you a public URL like:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8080
```

Copy the `https://abc123.ngrok.io` URL (yours will be different).

### 6. Configure Vapi to use your transcriber

In your Vapi assistant configuration, set the transcriber:

```json
{
  "transcriber": {
    "provider": "custom-transcriber",
    "server": {
      "url": "wss://abc123.ngrok.io/api/custom-transcriber"
    }
  }
}
```

**Note:** Change `https://` to `wss://` for the WebSocket URL!

### 7. Test your Vapi assistant

Make a call to your Vapi assistant. The transcription will now be powered by Soniox!

## 🔧 Configuration

### Server Configuration

You can customize the server using environment variables in your `.env` file:

```bash
# Server host (default: 0.0.0.0)
VAPI_SERVER_HOST=0.0.0.0

# Server port (default: 8080)
VAPI_SERVER_PORT=8080
```

### Soniox Configuration

Edit [src/soniox_transcriber/vapi_server.py](src/soniox_transcriber/vapi_server.py) to customize:

```python
def get_soniox_config(self) -> dict:
    config = {
        "model": "stt-rt-preview",  # Soniox model
        "language_hints": ["en"],    # Add more languages: ["en", "es", "fr"]
        "enable_endpoint_detection": True,
        # Add more Soniox features as needed
    }
```

## 📊 How It Works

```
┌──────┐           ┌─────────────────┐           ┌─────────┐
│ Vapi │  Audio    │  Your Server    │  Audio    │ Soniox  │
│      │ ────────> │ (vapi_server.py)│ ────────> │   API   │
│      │           │                 │           │         │
│      │ Text      │                 │ Text      │         │
│      │ <──────── │                 │ <──────── │         │
└──────┘           └─────────────────┘           └─────────┘
```

1. **Vapi connects** to your server via WebSocket
2. **Audio streams** from Vapi's call to your server
3. **Your server forwards** audio to Soniox API
4. **Soniox transcribes** and returns text
5. **Your server sends** transcription back to Vapi
6. **Vapi uses** the transcription in the conversation

## 🔐 Authentication

### Optional: Add authentication to your server

If you want to secure your transcriber endpoint, you can configure Vapi credentials:

**In Vapi Dashboard:**
1. Go to Credentials
2. Create a new Custom Credential
3. Choose authentication type (Bearer Token recommended)
4. Save the credential ID

**Update your Vapi config:**
```json
{
  "transcriber": {
    "provider": "custom-transcriber",
    "server": {
      "url": "wss://abc123.ngrok.io/api/custom-transcriber",
      "credentialId": "your-credential-id"
    }
  }
}
```

**Update your server to validate tokens:**
See Vapi documentation for implementing authentication in your custom transcriber.

## 🌐 Production Deployment

For production, instead of ngrok, deploy your server to:

### Option 1: Deploy to a Cloud Platform

**Render, Railway, or similar:**
1. Push your code to GitHub
2. Connect your repository to the platform
3. Set environment variables (SONIOX_API_KEY)
4. Deploy and get a permanent URL
5. Use that URL in Vapi config

**Environment variables needed:**
```
SONIOX_API_KEY=your_key
VAPI_SERVER_HOST=0.0.0.0
VAPI_SERVER_PORT=8080
```

### Option 2: Use a VPS (DigitalOcean, AWS, etc.)

```bash
# On your VPS
git clone your-repo
cd soniox_transcriber
pip install -e .

# Set environment variables
export SONIOX_API_KEY=your_key

# Run with a process manager
pm2 start "soniox-vapi-server" --name vapi-transcriber

# Configure nginx reverse proxy for wss://
```

### Option 3: Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

ENV VAPI_SERVER_HOST=0.0.0.0
ENV VAPI_SERVER_PORT=8080

CMD ["soniox-vapi-server"]
```

Deploy to your preferred container platform.

## 🐛 Troubleshooting

### Server won't start
- Check that port 8080 is available: `lsof -i :8080`
- Make sure SONIOX_API_KEY is set in `.env`
- Install dependencies: `uv sync`

### Vapi can't connect
- Verify ngrok is running and showing the correct URL
- Change `https://` to `wss://` in Vapi config
- Check firewall settings if self-hosting

### No transcriptions appearing
- Check server logs for errors
- Verify Soniox API key is valid and has credits
- Test Soniox connection: `uv run soniox-transcriber`
- Check Vapi logs in their dashboard

### Audio format errors
- The server automatically configures based on Vapi's audio format
- Default: 16kHz, stereo, PCM S16LE
- Check server logs for audio config received from Vapi

### Connection drops
- ngrok free tier may disconnect after a few hours
- For production, use a permanent deployment
- Check your internet connection stability

## 📝 Example Vapi Assistant Config

Complete example of a Vapi assistant using Soniox:

```json
{
  "name": "My Assistant",
  "model": {
    "provider": "openai",
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      }
    ]
  },
  "transcriber": {
    "provider": "custom-transcriber",
    "server": {
      "url": "wss://your-server.ngrok.io/api/custom-transcriber"
    }
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "your-voice-id"
  }
}
```

## 🎯 Benefits of Using Soniox with Vapi

- **Superior accuracy**: Soniox offers industry-leading transcription quality
- **Low latency**: Real-time transcription optimized for voice AI
- **Custom vocabulary**: Add domain-specific terms via context
- **Language support**: Multiple languages and automatic detection
- **Speaker diarization**: Distinguish between different speakers
- **Endpoint detection**: Automatically detects when user stops speaking

## 📚 Additional Resources

- [Vapi Documentation](https://docs.vapi.ai)
- [Soniox Documentation](https://soniox.com/docs)
- [Vapi Custom Transcriber Docs](https://docs.vapi.ai/customization/custom-transcriber)
- [ngrok Documentation](https://ngrok.com/docs)

## 💡 Tips

- **Monitor logs**: Watch server output to debug issues
- **Test locally first**: Use ngrok before deploying to production
- **Keep ngrok running**: Don't close the ngrok terminal while testing
- **Update Vapi config**: Remember to update URL if ngrok restarts
- **Check credits**: Monitor your Soniox API usage at console.soniox.com

## 🆘 Need Help?

- Check server logs for error messages
- Verify all URLs are correct (wss:// not https://)
- Test with the console transcriber first: `uv run soniox-transcriber`
- Ensure Soniox API key is valid
- Check Vapi dashboard for connection errors
