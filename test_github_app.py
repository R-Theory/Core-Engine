#!/usr/bin/env python3
"""
Test GitHub App connection directly
"""
import requests
import json
import sys

def test_github_app():
    # Test the public GitHub App endpoint
    print("🧪 Testing GitHub App connection...")

    # You'll need to paste your private key here temporarily for testing
    private_key = input("Paste your private key (entire .pem content): ")

    data = {
        "app_id": "1968268",
        "installation_id": "86374982",
        "private_key": private_key
    }

    try:
        # Test via public endpoint
        response = requests.post(
            "http://localhost:8000/github-app/test",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))

        if result.get("success"):
            print("\n✅ GitHub App connection is working!")
            print("✅ Credentials are valid!")

            # Show what repositories are accessible
            if "repos" in result.get("details", {}):
                repos = result["details"]["repos"]
                print(f"\n📁 Found {len(repos)} repositories:")
                for repo in repos[:5]:  # Show first 5
                    print(f"  - {repo}")
        else:
            print("\n❌ GitHub App connection failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_github_app()