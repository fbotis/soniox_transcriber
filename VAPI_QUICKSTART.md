# Vapi Integration - Quick Start

Get Soniox working with Vapi in 5 minutes!

## 🚀 Setup (One Time)

```bash
# 1. Install ngrok (if not already installed)
brew install ngrok

# 2. Install dependencies
uv sync
```

## ▶️ Running the Server

### Terminal 1: Start the Transcriber Server
```bash
uv run soniox-vapi-server
```

You should see:
```
🚀 SONIOX VAPI CUSTOM TRANSCRIBER SERVER
📡 Server starting on 0.0.0.0:8080
✅ Server ready - waiting for connections...
```

### Terminal 2: Expose with ngrok
```bash
ngrok http 8080
```

Copy the **Forwarding** URL (e.g., `https://abc123.ngrok.io`)

## 🔧 Configure Vapi

In your Vapi assistant config:

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

**Important:** Use `wss://` (not `https://`) for the WebSocket URL!

## ✅ Test

1. Call your Vapi assistant
2. Speak into the phone
3. Watch transcriptions appear in your server terminal
4. Vapi should respond based on the Soniox transcription

## 📝 Example Server Output

When a call comes in:
```
📞 New Vapi connection received
📥 Received Vapi start message: {'sampleRate': 16000, 'channels': 2}
✅ Connected to Soniox (sample_rate=16000, channels=2)
📤 Sent to Vapi: Hello, how can I help you today?
📤 Sent to Vapi: I need assistance with my account.
Session ended
```

## 🐛 Troubleshooting

**Server won't start:**
- Check `.env` has `SONIOX_API_KEY`
- Port 8080 already in use? Change with `VAPI_SERVER_PORT=8081`

**Vapi can't connect:**
- Verify ngrok is running
- Use `wss://` not `https://` in Vapi config
- Copy the full ngrok URL including subdomain

**No transcriptions:**
- Check server logs for errors
- Verify Soniox API key is valid at console.soniox.com
- Check Vapi dashboard for connection errors

## 📚 Full Documentation

See [VAPI_INTEGRATION.md](VAPI_INTEGRATION.md) for:
- Production deployment
- Authentication setup
- Advanced configuration
- Complete troubleshooting guide

## 💡 Pro Tips

- Keep both terminals open while testing
- ngrok URL changes each restart (free tier)
- For production, deploy to a cloud platform
- Monitor server logs for debugging
