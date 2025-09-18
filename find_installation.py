#!/usr/bin/env python3
"""
Simple script to find GitHub App Installation ID
"""
import requests
import json

def find_installation_id():
    app_id = "1968268"

    # Read private key from file
    try:
        with open("private-key.pem", "r") as f:
            private_key = f.read()
    except FileNotFoundError:
        print("Please save your GitHub App private key as 'private-key.pem' in this directory")
        return

    # Prepare the request
    data = {
        "app_id": app_id,
        "private_key": private_key
    }

    try:
        response = requests.post(
            "http://localhost:8000/github-app/list-installations",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Here are your installations:")
            print(json.dumps(result, indent=2))

            if "installations" in result and result["installations"]:
                installation_id = result["installations"][0]["id"]
                print(f"\n🎯 Your Installation ID is: {installation_id}")
                print(f"\nNow use these values in Core Engine:")
                print(f"- App ID: {app_id}")
                print(f"- Installation ID: {installation_id}")
                print("- Private Key: (paste the entire contents of your .pem file)")
            else:
                print("\n❌ No installations found. Make sure you've installed your GitHub App.")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_installation_id()