#!/usr/bin/env python3
"""
Script to update a Vapi assistant with Soniox custom transcriber
"""
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def patch_vapi_assistant(vapi_api_key: str, assistant_id: str, transcriber_url: str):
    """Update an existing Vapi assistant with custom transcriber."""

    url = f"https://api.vapi.ai/assistant/{assistant_id}"
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "transcriber": {
            "provider": "custom-transcriber",
            "server": {
                "url": transcriber_url
            }
        }
    }

    print("Updating Vapi assistant with Soniox transcriber...")
    print(f"Assistant ID: {assistant_id}")
    print(f"Transcriber URL: {transcriber_url}")

    # Print curl command
    import json
    print("\n" + "=" * 60)
    print("📋 Equivalent curl command:")
    print("=" * 60)
    curl_cmd = f"""curl -X PATCH {url} \\
  -H "Authorization: Bearer {vapi_api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload, indent=2)}'"""
    print(curl_cmd)
    print("=" * 60 + "\n")

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ Success! Assistant updated:")
        print(f"   ID: {data.get('id')}")
        print(f"   Name: {data.get('name')}")
        print(f"   Transcriber: custom-transcriber")
        print(f"   Transcriber URL: {transcriber_url}")
        return data
    else:
        print(f"\n❌ Error updating assistant:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == 404:
            print("\n⚠️  Assistant not found. Check your VAPI_ASSISTANT_ID.")
        elif "custom-transcriber" in response.text.lower() and "not supported" in response.text.lower():
            print("\n⚠️  Custom transcriber is not available on your Vapi plan.")
            print("   Options:")
            print("   1. Upgrade your Vapi plan")
            print("   2. Contact Vapi support to enable custom transcriber")

        return None


def main():
    print("\n" + "=" * 60)
    print("VAPI ASSISTANT UPDATER - SONIOX CUSTOM TRANSCRIBER")
    print("=" * 60 + "\n")

    # Get Vapi API key
    vapi_api_key = os.environ.get("VAPI_API_KEY")
    if not vapi_api_key:
        print("❌ VAPI_API_KEY not found in environment")
        print("\nPlease add to .env file:")
        print("VAPI_API_KEY=your_vapi_api_key")
        sys.exit(1)

    # Get assistant ID
    assistant_id = os.environ.get("VAPI_ASSISTANT_ID")
    if not assistant_id:
        print("❌ VAPI_ASSISTANT_ID not found in environment")
        print("\nPlease add to .env file:")
        print("VAPI_ASSISTANT_ID=your_assistant_id")
        print("\nYou can find your assistant ID in the Vapi dashboard URL:")
        print("https://dashboard.vapi.ai/assistants/YOUR_ASSISTANT_ID")
        sys.exit(1)

    # Get transcriber URL
    transcriber_url = os.environ.get("VAPI_TRANSCRIBER_URL")
    if not transcriber_url:
        print("❌ VAPI_TRANSCRIBER_URL not found in environment")
        print("\nPlease add to .env file:")
        print("VAPI_TRANSCRIBER_URL=wss://your-ngrok-url.ngrok.io/api/custom-transcriber")
        print("\nGet your ngrok URL by running: ngrok http 8080")
        sys.exit(1)

    # Validate URL format
    if not transcriber_url.startswith("wss://"):
        print("\n⚠️  Warning: VAPI_TRANSCRIBER_URL should start with wss://")
        print(f"Current value: {transcriber_url}")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Aborted. Please update VAPI_TRANSCRIBER_URL in .env")
            sys.exit(0)

    # Update assistant
    result = patch_vapi_assistant(vapi_api_key, assistant_id, transcriber_url)

    if result:
        print("\n" + "=" * 60)
        print("Assistant updated! Test it in the Vapi dashboard.")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("Assistant update failed. See error above.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
