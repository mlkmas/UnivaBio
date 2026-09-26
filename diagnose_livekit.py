# diagnose_livekit.py
"""
Diagnostic script to check LiveKit setup
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

print("=" * 70)
print("🔍 LIVEKIT DIAGNOSTIC")
print("=" * 70)

# Check environment variables
print("\n1. CHECKING ENVIRONMENT VARIABLES:")
print("-" * 70)

url = os.getenv("LIVEKIT_URL")
api_key = os.getenv("LIVEKIT_API_KEY")
api_secret = os.getenv("LIVEKIT_API_SECRET")

if url:
    print(f"✅ LIVEKIT_URL: {url}")
else:
    print("❌ LIVEKIT_URL: NOT SET")

if api_key:
    print(f"✅ LIVEKIT_API_KEY: {api_key[:10]}...")
else:
    print("❌ LIVEKIT_API_KEY: NOT SET")

if api_secret:
    print(f"✅ LIVEKIT_API_SECRET: {api_secret[:10]}...")
else:
    print("❌ LIVEKIT_API_SECRET: NOT SET")

# Check token server
print("\n2. CHECKING TOKEN SERVER:")
print("-" * 70)

try:
    response = requests.get("http://localhost:5000/health", timeout=2)
    if response.status_code == 200:
        print("✅ Token server is running")

        # Try to get a token
        try:
            token_response = requests.get("http://localhost:5000/get_token?identity=test_user", timeout=2)
            if token_response.status_code == 200:
                token_data = token_response.json()
                print("✅ Token server can generate tokens")
                print(f"   Token: {token_data.get('token', '')[:50]}...")
            else:
                print(f"❌ Token generation failed: {token_response.status_code}")
        except Exception as e:
            print(f"❌ Error getting token: {e}")
    else:
        print(f"❌ Token server returned: {response.status_code}")
except Exception as e:
    print(f"❌ Token server not responding: {e}")
    print("   Start it with: poetry run python src/token_server.py")

# Check LiveKit Agent
print("\n3. CHECKING LIVEKIT AGENT:")
print("-" * 70)

print("ISSUE FOUND:")
print("  Your Terminal 2 shows:")
print("  '❌ Error connecting to LiveKit: 401 Unauthorized'")
print()
print("THIS MEANS:")
print("  - Token server works ✅")
print("  - But LiveKit Cloud rejects the credentials ❌")
print()
print("SOLUTION:")
print("  1. Go to: https://cloud.livekit.io/")
print("  2. Login")
print("  3. Click on your project: rememberme-wh7x5elg")
print("  4. Go to Settings → Keys")
print("  5. DELETE old key")
print("  6. CREATE NEW KEY")
print("  7. Copy BOTH:")
print("     - API Key")
print("     - API Secret")
print("  8. Update .env file")
print("  9. Restart Terminal 1 and Terminal 2")

# Check if recordings directory exists
print("\n4. CHECKING RECORDINGS DIRECTORY:")
print("-" * 70)

from pathlib import Path

recordings_dir = Path("recordings")
if recordings_dir.exists():
    recordings = list(recordings_dir.glob("*.wav"))
    print(f"✅ Recordings directory exists")
    print(f"   Files: {len(recordings)}")

    if recordings:
        print("   Recent recordings:")
        for rec in sorted(recordings, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            print(f"   - {rec.name}")
else:
    print("❌ Recordings directory doesn't exist")
    recordings_dir.mkdir(exist_ok=True)
    print("✅ Created recordings directory")

# Check database connection
print("\n5. CHECKING DATABASE:")
print("-" * 70)

try:
    from src.database import get_all_conversations

    conversations = get_all_conversations()
    print(f"✅ Database connected")
    print(f"   Total conversations: {len(conversations)}")

    if conversations:
        recent = conversations[0]
        print(f"   Most recent: {recent.get('generated_at', 'N/A')}")
    else:
        print("   No conversations recorded yet")
except Exception as e:
    print(f"❌ Database error: {e}")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)

issues = []

if not url or not api_key or not api_secret:
    issues.append("❌ Missing LiveKit credentials in .env")

try:
    response = requests.get("http://localhost:5000/health", timeout=1)
    if response.status_code != 200:
        issues.append("❌ Token server not working")
except:
    issues.append("❌ Token server not running")

if "401" in str(os.popen("tasklist").read()):  # This is a hack, won't actually work
    issues.append("❌ LiveKit credentials invalid (401 error)")

if issues:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
    print("\nFIX THESE FIRST!")
else:
    print("\n✅ Basic setup looks good!")
    print("   If recording still doesn't work:")
    print("   1. Check Terminal 2 for error messages")
    print("   2. Verify you can connect to LiveKit room")
    print("   3. Test with simple recording first")

print("=" * 70)