# src/background_scheduler.py
"""
Background scheduler for automatic medication reminders and daily recaps.
Run this in a separate terminal: poetry run python src/background_scheduler.py
"""
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Fix import path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_all_medications, update_medication, get_settings
from src.smart_reminder import generate_smart_reminder
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech

# Directory for scheduled audio files
SCHEDULED_AUDIO_DIR = Path("scheduled_audio")
SCHEDULED_AUDIO_DIR.mkdir(exist_ok=True)


def check_medication_times():
    """Check if any medications are due and generate reminders"""
    try:
        medications = get_all_medications()
        now = datetime.now()
        today_name = now.strftime("%A")

        print(f"[DEBUG] Checking meds at {now.strftime('%H:%M:%S')}")

        for med in medications:
            med_id = str(med.get('_id') or med.get('id'))
            med_time_str = med.get('time_to_take', '')

            try:
                # Parse the scheduled time
                scheduled_time = datetime.strptime(med_time_str, '%I:%M %p').time()
            except ValueError:
                continue

            # FIXED LOGIC: Check if we're within the current minute
            current_time = now.time()
            current_minute = current_time.replace(second=0, microsecond=0)
            scheduled_minute = scheduled_time.replace(second=0, microsecond=0)

            # Only trigger if we're in the exact minute
            if current_minute != scheduled_minute:
                continue

            print(f"[DEBUG] Time match for {med.get('name')} at {med_time_str}")

            # Check if it should be reminded today
            stype = med.get('schedule_type')
            should_remind_today = False

            if stype == 'Daily':
                should_remind_today = True
            elif stype == 'Weekly':
                if today_name in med.get('days_of_week', []):
                    should_remind_today = True
            elif stype == 'One-Time':
                sdate = med.get('specific_date')
                if isinstance(sdate, datetime) and sdate.date() == now.date():
                    should_remind_today = True

            if not should_remind_today:
                print(f"[DEBUG] Not scheduled for today: {med.get('name')}")
                continue

            # Check if already reminded in the last 2 minutes (prevent duplicates)
            last_reminded = med.get('last_reminded')
            if last_reminded:
                if isinstance(last_reminded, str):
                    last_reminded = datetime.fromisoformat(last_reminded)

                time_since_reminder = (now - last_reminded).total_seconds() / 60
                if time_since_reminder < 2:
                    print(f"[DEBUG] Already reminded recently: {med.get('name')}")
                    continue

            # TRIGGER REMINDER
            print(f"\n⏰ TRIGGER: Medication '{med.get('name')}' at {med_time_str}")
            audio_path = generate_smart_reminder(med)

            if audio_path:
                # Save to scheduled directory
                scheduled_filename = f"med_{med_id}_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
                scheduled_path = SCHEDULED_AUDIO_DIR / scheduled_filename

                import shutil
                shutil.copy(str(audio_path), str(scheduled_path))

                print(f"✅ Medication reminder saved: {scheduled_path}")

                # Update last_reminded
                update_medication(med_id, {"last_reminded": now})

                # Clean up temp file
                try:
                    os.remove(audio_path)
                except:
                    pass

    except Exception as e:
        print(f"❌ Error checking medications: {e}")
        import traceback
        traceback.print_exc()


def check_daily_recap():
    """Check if it's time for daily recap"""
    try:
        settings = get_settings()

        if not settings.get('daily_recap_enabled', True):
            return

        now = datetime.now()

        # Check if recap already generated today
        recap_marker = SCHEDULED_AUDIO_DIR / f"recap_{now.strftime('%Y%m%d')}.marker"
        if recap_marker.exists():
            return

        # Get scheduled time
        recap_time_str = settings.get('daily_recap_time', '19:00')
        try:
            scheduled_time = datetime.strptime(recap_time_str, '%H:%M').time()
        except ValueError:
            return

        # Check if we're within the current minute
        current_time = now.time()
        current_minute = current_time.replace(second=0, microsecond=0)
        scheduled_minute = scheduled_time.replace(second=0, microsecond=0)

        if current_minute != scheduled_minute:
            return

        # TRIGGER RECAP
        print(f"\n🌅 TRIGGER: Daily Recap at {recap_time_str}")

        recap_script = generate_daily_recap()
        audio_path = text_to_speech(recap_script, output_filename="temp_scheduled_recap.mp3")

        if audio_path:
            scheduled_filename = f"recap_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
            scheduled_path = SCHEDULED_AUDIO_DIR / scheduled_filename

            import shutil
            shutil.copy(str(audio_path), str(scheduled_path))

            print(f"✅ Daily recap saved: {scheduled_path}")

            # Create marker
            recap_marker.touch()

            # Clean up
            try:
                os.remove(audio_path)
            except:
                pass

    except Exception as e:
        print(f"❌ Error checking daily recap: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main scheduler loop"""
    print("=" * 50)
    print("🤖 RememberMe Background Scheduler (FIXED)")
    print("=" * 50)
    print("Monitoring for:")
    print("  - Medication times")
    print("  - Daily recap schedule")
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        while True:
            current_time_str = datetime.now().strftime("%H:%M:%S")
            print(f"⏱️  Checking... {current_time_str}", end="\r")

            # Check medications
            check_medication_times()

            # Check daily recap
            check_daily_recap()

            # Wait 30 seconds (check twice per minute)
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped")


if __name__ == "__main__":
    main()