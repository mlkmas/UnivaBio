# quick_test_medication.py
"""
Creates a medication reminder for EXACTLY 2 minutes from now
Run this to test the medication reminder system
"""
from datetime import datetime, timedelta
from src.database import add_medication
from src.schemas import Medication

# Calculate exact time 2 minutes from now
now = datetime.now()
reminder_time = now + timedelta(minutes=2)

# Round to nearest minute
reminder_time = reminder_time.replace(second=0, microsecond=0)

time_str = reminder_time.strftime("%I:%M %p")

print("=" * 70)
print("🧪 MEDICATION REMINDER TEST")
print("=" * 70)
print(f"Current time:     {now.strftime('%I:%M:%S %p')}")
print(f"Reminder set for: {time_str}")
print(f"Wait time:        ~2 minutes")
print("=" * 70)

# Create test medication
test_med = Medication(
    name="Test Vitamin",
    dosage="1 tablet",
    purpose="Testing automatic reminders",
    time_to_take=time_str,
    schedule_type="Daily"
)

# Add to database
try:
    med_id = add_medication(test_med)

    if med_id:
        print("✅ Test medication created successfully!")
        print()
        print("WHAT TO EXPECT:")
        print(f"1. At {time_str}, Terminal 3 (scheduler) will show:")
        print(f"   ⏰ MEDICATION TIME: Test Vitamin at {time_str}")
        print()
        print("2. Audio will be generated automatically")
        print()
        print("3. File saved to: scheduled_audio/med_*.mp3")
        print()
        print("4. Go to Patient View - audio will AUTO-PLAY!")
        print()
        print("WATCH THESE TERMINALS:")
        print("  Terminal 3: Background Scheduler (will generate audio)")
        print("  Terminal 4: Patient View (will auto-play audio)")
        print()
        print(f"⏰ SET ALARM FOR: {time_str}")
        print()
        print("If it doesn't work, check:")
        print("  - Terminal 3 is running (background_scheduler.py)")
        print("  - Current system time matches expected time")
        print("  - Check scheduled_audio/ folder for files")
    else:
        print("❌ Failed to create medication")

except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 70)