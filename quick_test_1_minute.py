# quick_test_1_minute.py
"""
ULTRA QUICK TEST - Sets medication for 1 MINUTE from now
"""
from datetime import datetime, timedelta
from src.database import add_medication, get_all_medications, delete_medication
from src.schemas import Medication

print("=" * 70)
print("⚡ ULTRA QUICK TEST - 1 MINUTE")
print("=" * 70)

# Clean up old test medications first
print("\n1. Cleaning old test medications...")
all_meds = get_all_medications()
for med in all_meds:
    if "Test" in med.get('name', '') or "Demo" in med.get('name', ''):
        med_id = str(med.get('_id') or med.get('id'))
        delete_medication(med_id)
        print(f"   Deleted: {med.get('name')}")

# Calculate time 1 MINUTE from now
now = datetime.now()
reminder_time = now + timedelta(minutes=1)
reminder_time = reminder_time.replace(second=0, microsecond=0)
time_str = reminder_time.strftime("%I:%M %p")

print(f"\n2. Creating test medication...")
print(f"   Current time:     {now.strftime('%I:%M:%S %p')}")
print(f"   Reminder set for: {time_str}")
print(f"   Wait time:        ~60 seconds")

# Create test medication
test_med = Medication(
    name="Test Vitamin",
    dosage="1 tablet",
    purpose="Quick test for presentation",
    time_to_take=time_str,
    schedule_type="Daily"
)

try:
    med_id = add_medication(test_med)

    if med_id:
        print("   ✅ Test medication created!")
    else:
        print("   ❌ Failed to create medication")
        exit(1)

except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ TEST READY!")
print("=" * 70)
print()
print("WHAT WILL HAPPEN IN ~60 SECONDS:")
print(f"1. At {time_str}, background scheduler will:")
print("   - Generate audio for 'Test Vitamin'")
print("   - Save to scheduled_audio/med_*.mp3")
print()
print("2. Patient View (refreshes every 30s) will:")
print("   - Auto-detect the new audio file")
print("   - Show '💊 Time for your medication!'")
print("   - Auto-play the reminder")
print()
print("WATCH THESE TERMINALS:")
print("  Terminal 1: Token Server")
print("  Terminal 2: Background Scheduler ⭐ WATCH THIS ONE")
print("  Terminal 3: Streamlit (Patient View)")
print()
print(f"⏰ ALARM: {time_str} (in ~1 minute)")
print()
print("TIP: Keep Patient View page open!")
print("=" * 70)