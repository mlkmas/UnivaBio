# quick_demo_test.py
"""
Quick test for presentation demo
Creates a medication reminder for 1 minute from now
"""
from datetime import datetime, timedelta
from src.database import add_medication, get_all_medications
from src.schemas import Medication

print("=" * 70)
print("🎯 QUICK DEMO TEST")
print("=" * 70)

# First, clear any test medications
print("\n1. Cleaning up old test medications...")
all_meds = get_all_medications()
from src.database import delete_medication

for med in all_meds:
    if "Demo" in med.get('name', '') or "Test" in med.get('name', ''):
        med_id = str(med.get('_id') or med.get('id'))
        delete_medication(med_id)
        print(f"   Deleted: {med.get('name')}")

# Calculate time 1 minute from now
now = datetime.now()
reminder_time = now + timedelta(minutes=1)
reminder_time = reminder_time.replace(second=0, microsecond=0)
time_str = reminder_time.strftime("%I:%M %p")

print(f"\n2. Creating demo medication...")
print(f"   Current time:     {now.strftime('%I:%M:%S %p')}")
print(f"   Reminder set for: {time_str}")

# Create demo medication
demo_med = Medication(
    name="Demo Vitamin",
    dosage="1 tablet",
    purpose="Demo for presentation",
    time_to_take=time_str,
    schedule_type="Daily"
)

try:
    med_id = add_medication(demo_med)

    if med_id:
        print("   ✅ Demo medication created!")
    else:
        print("   ❌ Failed to create medication")
        exit(1)

except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n3. Testing auto-refresh system...")
from pathlib import Path

scheduled_dir = Path("scheduled_audio")
scheduled_dir.mkdir(exist_ok=True)
print(f"   ✅ Scheduled audio directory ready")

print("\n" + "=" * 70)
print("✅ DEMO READY!")
print("=" * 70)
print()
print("WHAT WILL HAPPEN:")
print(f"1. At {time_str}, background scheduler will:")
print("   - Generate medication reminder audio")
print("   - Save to scheduled_audio/")
print()
print("2. Patient View (auto-refreshes every 30s) will:")
print("   - Detect new audio file")
print("   - Show '💊 Time for your medication!'")
print("   - Auto-play the reminder")
print()
print("TERMINALS TO WATCH:")
print("  Terminal 1: Token Server (poetry run python src/token_server.py)")
print("  Terminal 2: Background Scheduler (poetry run python src/background_scheduler.py)")
print("  Terminal 3: Streamlit (poetry run streamlit run app.py)")
print()
print(f"⏰ DEMO TIME: {time_str} (in ~1 minute)")
print()
print("=" * 70)