#!/usr/bin/env python3
"""
Script to initiate a test call with your Vapi assistant
"""
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def create_test_call(vapi_api_key: str, assistant_id: str, phone_number: str):
    """Create a test call to your assistant."""

    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }

    # For web/test call (not phone)
    payload = {
        "assistantId": assistant_id,
        "type": "webCall"  # Use webCall for testing without a phone
    }

    # If you want to call a real phone number:
    # payload = {
    #     "assistantId": assistant_id,
    #     "customer": {
    #         "number": phone_number
    #     }
    # }

    print(f"Creating test call with assistant: {assistant_id}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        data = response.json()
        print("\n✅ Success! Call created:")
        print(f"   Call ID: {data.get('id')}")
        print(f"   Status: {data.get('status')}")

        if data.get('webCallUrl'):
            print(f"\n🔗 Open this URL to join the call:")
            print(f"   {data.get('webCallUrl')}")

        return data
    else:
        print(f"\n❌ Error creating call:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def main():
    print("\n" + "=" * 60)
    print("VAPI TEST CALL - SONIOX TRANSCRIBER")
    print("=" * 60 + "\n")

    # Get Vapi API key
    vapi_api_key = os.environ.get("VAPI_API_KEY")
    if not vapi_api_key:
        print("❌ VAPI_API_KEY not found in environment")
        print("Please add it to your .env file")
        sys.exit(1)

    # Get assistant ID
    print("Enter your assistant ID")
    print("(You can find this in the Vapi dashboard or from the create script)")
    assistant_id = input("\nAssistant ID: ").strip()

    if not assistant_id:
        print("❌ Assistant ID is required")
        sys.exit(1)

    print("\n⚠️  Make sure your server is running:")
    print("   Terminal 1: uv run soniox-vapi-server")
    print("   Terminal 2: ngrok http 8080")

    confirm = input("\nServers running? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Start your servers first, then try again!")
        sys.exit(0)

    # Create test call
    result = create_test_call(vapi_api_key, assistant_id, None)

    if result:
        print("\n" + "=" * 60)
        print("Call created! Check your server logs for transcriptions.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
