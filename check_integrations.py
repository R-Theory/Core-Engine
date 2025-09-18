#!/usr/bin/env python3
"""
Check what integrations are saved and configured
"""
import requests
import json

def check_saved_integrations():
    print("🔍 Checking saved integrations...")

    # You'll need your login credentials
    username = input("Username/Email: ")
    password = input("Password: ")

    try:
        # First login to get token
        login_response = requests.post(
            "http://localhost:3000/api/v1/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return

        login_data = login_response.json()
        token = login_data.get("access_token")

        if not token:
            print("❌ No access token received")
            return

        print("✅ Login successful!")

        # Now check integrations
        headers = {"Authorization": f"Bearer {token}"}

        # Check available integrations
        available_response = requests.get(
            "http://localhost:3000/api/v1/settings/integrations/available",
            headers=headers
        )

        if available_response.status_code == 200:
            available = available_response.json()
            print("\n📋 Available integrations:")
            for name, details in available.items():
                print(f"  - {details['service_name']} ({name})")

        # Check configured integrations
        configured_response = requests.get(
            "http://localhost:3000/api/v1/settings/integrations",
            headers=headers
        )

        if configured_response.status_code == 200:
            configured = configured_response.json()
            print(f"\n⚙️ Configured integrations: {len(configured)}")
            for integration in configured:
                print(f"  - {integration.get('service_display_name', 'Unknown')}: {integration.get('connection_status', 'unknown')}")
                if integration.get('connection_error'):
                    print(f"    Error: {integration['connection_error']}")
        else:
            print(f"❌ Failed to get configured integrations: {configured_response.status_code}")
            print(configured_response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_saved_integrations()