"""
Test script to debug Devin API authentication and list secrets
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEVIN_API_KEY")
org_id = os.getenv("DEVIN_ORG_ID")
api_url = os.getenv("DEVIN_API_URL", "https://api.devin.ai")

print(f"API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
print(f"Org ID: {org_id}")
print(f"API URL: {api_url}")

# List secrets using v3 API
print("\n=== List Secrets (v3 API) ===")
secrets_url = f"{api_url}/v3/organizations/{org_id}/secrets"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(secrets_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        secrets = data.get('data', [])
        print(f"✓ Found {len(secrets)} secrets:")
        for secret in secrets:
            print(f"  - Name: {secret.get('key')}")
            print(f"    ID: {secret.get('secret_id')}")
            print(f"    Type: {secret.get('secret_type')}")
            print(f"    Created: {secret.get('created_at')}")
            print()
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Create secret using v3 API with different name
print("\n=== Create GitHub Token Secret (v3 API) ===")
print("You need to create a GitHub Personal Access Token first:")
print("1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)")
print("2. Click 'Generate new token (classic)'")
print("3. Name it 'Devin Automation'")
print("4. Select 'repo' permissions")
print("5. Generate and copy the token")
print("\nThen paste your GitHub token here:")
github_token = input("GitHub Token: ").strip()

if github_token:
    create_secret_url = f"{api_url}/v3/organizations/{org_id}/secrets"
    payload = {
        "type": "key-value",
        "key": "GITHUB_TOKEN_AUTOMATION",
        "value": github_token,
        "is_sensitive": True,
        "note": "GitHub token for pushing to repositories"
    }
    
    try:
        response = requests.post(create_secret_url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Secret created successfully!")
            print(f"Secret ID: {data.get('secret_id')}")
            print(f"\nAdd this to your .env file:")
            print(f"DEVIN_GITHUB_SECRET_ID={data.get('secret_id')}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
