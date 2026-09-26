# test_recap_now.py
"""
Test the daily recap feature immediately by generating it manually
"""
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("🌅 TESTING DAILY RECAP NOW")
print("=" * 70)

# Create scheduled_audio directory
scheduled_dir = Path("scheduled_audio")
scheduled_dir.mkdir(exist_ok=True)

print("\n1. Generating daily recap...")
try:
    recap_script = generate_daily_recap()
    print(f"   ✅ Recap generated!")
    print(f"   Preview: {recap_script[:100]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n2. Converting to speech...")
try:
    audio_path = text_to_speech(recap_script, "temp_test_recap.mp3")
    print(f"   ✅ Audio created: {audio_path}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n3. Saving to scheduled_audio/...")
try:
    now = datetime.now()
    scheduled_filename = f"recap_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
    scheduled_path = scheduled_dir / scheduled_filename

    import shutil

    shutil.copy(str(audio_path), str(scheduled_path))

    print(f"   ✅ Saved: {scheduled_path}")

    # Clean up temp file
    audio_path.unlink()

except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ SUCCESS!")
print("=" * 70)
print()
print("NOW DO THIS:")
print("1. Go to Patient View page")
print("2. You should see: '🌅 Here's your daily recap!'")
print("3. Audio should auto-play")
print()
print("If nothing happens:")
print("- Wait 30 seconds (page auto-refreshes)")
print("- Or manually refresh the page")
print()
print("=" * 70)