# pages/2_Patient_View.py
import streamlit as st
from datetime import datetime, time
from src.database import get_all_medications, get_all_people, get_settings
from src.recap_generator import generate_daily_recap
from src.text_to_speech import text_to_speech
from src.patient_assistant import answer_patient_question
from src.transcriber import transcribe_audio
from src.smart_reminder import generate_smart_reminder  # Added import
import os
import re
from pathlib import Path
import tempfile
import time as time_module
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Patient View", page_icon="😊", layout="centered")

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 32px !important;
        font-weight: bold;
    }
    div[data-testid="stButton"] button {
        font-size: 24px;
        padding: 20px;
        height: auto;
    }
    .recording-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        font-size: 20px;
        font-weight: bold;
        animation: pulse 2s infinite;
        z-index: 9999;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    /* Style for the small play button */
    div[data-testid="stVerticalBlock"] .stButton button {
        font-size: 16px; /* Smaller font */
        padding: 5px 10px; /* Smaller padding */
        height: auto;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# REMOVED ALL AUTO-REFRESH
# ========================================

st.title("😊 Hello! Here is your day.")
st.caption(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")

# ========================================
# ADDED MANUAL REFRESH BUTTON
# ========================================
if st.button("🔄 Refresh for Reminders", use_container_width=True):
    # This button is now the only way to check for scheduled audio
    pass  # The page re-runs automatically, triggering the check below

# Load settings
settings = get_settings()
assistant_mode = settings.get('assistant_mode_enabled', False)
livekit_active = settings.get('livekit_session_active', False)

# Show recording indicator ("floating thing")
if livekit_active or assistant_mode:
    st.markdown('<div class="recording-indicator">🔴 Listening</div>', unsafe_allow_html=True)

st.divider()

# Load people profiles
try:
    people_profiles = {person['name'].lower(): person for person in get_all_people()}
except Exception as e:
    people_profiles = {}

# ========================================
# AUTO-CHECK FOR SCHEDULED AUDIO (FIXED)
# (This now only runs on manual refresh)
# ========================================
scheduled_audio_dir = Path("scheduled_audio")
if not scheduled_audio_dir.exists():
    scheduled_audio_dir.mkdir(exist_ok=True)

if 'played_files_session' not in st.session_state:
    st.session_state.played_files_session = set()

audio_files = list(scheduled_audio_dir.glob("*.mp3"))
if audio_files:
    audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for pending_audio in audio_files:
        audio_path_str = str(pending_audio)

        # Check if file *still exists* and *hasn't been played* this session
        if pending_audio.exists() and audio_path_str not in st.session_state.played_files_session:

            # 1. Add to session state FIRST to prevent re-playing
            st.session_state.played_files_session.add(audio_path_str)

            # 2. Show message
            if 'med_' in pending_audio.name:
                st.success(f"💊 Time for your medication!")
            elif 'recap_' in pending_audio.name:
                st.success(f"🌅 Here's your daily recap!")

            # 3. Play audio
            st.audio(audio_path_str, autoplay=True)

            # 4. --- THIS IS THE FIX ---
            #    Delete the file so it never plays again, even if app restarts
            try:
                pending_audio.unlink()
                print(f"Deleted played reminder: {audio_path_str}")
            except Exception as e:
                print(f"Error deleting {audio_path_str}: {e}")
            # 5. Do not break, allow all new files to play
# ========================================
# END OF FIX
# ========================================


# ========================================
# DAILY RECAP
# ========================================
st.header("What Happened Today?")

if 'recap_audio_path' not in st.session_state:
    st.session_state.recap_audio_path = None
if 'recap_script' not in st.session_state:
    st.session_state.recap_script = None

if st.button("Tell Me About My Day", use_container_width=True, type="primary"):
    with st.spinner("Thinking about your day..."):
        st.session_state.recap_script = generate_daily_recap()
        audio_path = text_to_speech(st.session_state.recap_script)
        st.session_state.recap_audio_path = str(audio_path)
        st.rerun()

if st.session_state.recap_script:
    st.subheader("Your Recap:")
    sentences = re.split(r'(?<=[.!?])\s+', st.session_state.recap_script)
    for sentence in sentences:
        if not sentence: continue
        found_person = None
        for name, profile in people_profiles.items():
            if name in sentence.lower():
                found_person = profile
                break
        if found_person:
            col_img, col_text = st.columns([1, 4])
            with col_img:
                photo_path = found_person['photo_url']
                if Path(photo_path).exists():
                    st.image(photo_path, width=80)
                else:
                    st.image("https://via.placeholder.com/150", width=80)
            with col_text:
                st.write(sentence)
        else:
            st.write(sentence)
    if st.session_state.recap_audio_path:
        if Path(st.session_state.recap_audio_path).exists():
            st.audio(str(st.session_state.recap_audio_path), autoplay=True)
            try:
                time_module.sleep(1)
                os.remove(st.session_state.recap_audio_path)
            except:
                pass
        st.session_state.recap_audio_path = None
else:
    st.info("Click the button to hear about your day!")

st.divider()

# ========================================
# MEDICATION SCHEDULE (WITH MANUAL PLAY)
# ========================================
st.header("Today's Medication Schedule")

if 'manual_med_audio' not in st.session_state:
    st.session_state.manual_med_audio = None

all_medications = get_all_medications()
todays_meds = []
today_date = datetime.now().date()
today_name = today_date.strftime('%A')

for med in all_medications:
    stype = med.get('schedule_type')
    is_today = False
    if stype == 'Daily':
        is_today = True
    elif stype == 'Weekly':
        if today_name in med.get('days_of_week', []): is_today = True
    elif stype == 'One-Time':
        sdate_raw = med.get('specific_date')
        sdate = sdate_raw.date() if isinstance(sdate_raw, datetime) else sdate_raw
        if sdate == today_date: is_today = True
    if is_today:
        todays_meds.append(med)

todays_meds.sort(key=lambda x: datetime.strptime(x.get('time_to_take', '12:00 AM'), '%I:%M %p').time())

if not todays_meds:
    st.success("No medications scheduled today. ✅")
else:
    for med in todays_meds:
        med_id = str(med.get('_id') or med.get('id'))
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"⏰ {med.get('time_to_take', '')} - {med.get('name', '')}")
            with col2:
                # RESTORED MANUAL PLAY BUTTON
                if st.button("🔊", key=f"play_med_{med_id}", help=f"Play reminder for {med.get('name')}"):
                    with st.spinner("Getting reminder..."):
                        # We generate a *new* audio file every time
                        audio_path = generate_smart_reminder(med)
                        st.session_state.manual_med_audio = audio_path
                        # We must rerun to show the new st.audio element
                        st.rerun()

            st.write(f"**Dosage:** {med.get('dosage', '')}")
            st.caption(f"**Purpose:** {med.get('purpose', '')}")
            st.caption("Press 🔄 above to check for auto-reminders.")

# Play manual medication audio if it exists
if st.session_state.manual_med_audio:
    audio_file = st.session_state.manual_med_audio
    if audio_file and Path(audio_file).exists():
        st.audio(audio_file, autoplay=True)
        try:
            time_module.sleep(1)  # Give it time to start playing
            os.remove(audio_file)
        except Exception as e:
            print(f"Error removing manual audio {audio_file}: {e}")
    # Clear the state so it doesn't play again on next button press
    st.session_state.manual_med_audio = None

st.divider()

# ========================================
# VOICE ASSISTANT (BELOW MEDICATIONS)
# ========================================
if assistant_mode:
    st.header("🤖 Ask Me a Question")
    st.caption("Click microphone, speak, then wait for my answer")
    if 'assistant_response' not in st.session_state:
        st.session_state.assistant_response = None
    if 'assistant_audio_path' not in st.session_state:
        st.session_state.assistant_audio_path = None
    if 'show_assistant_input' not in st.session_state:
        st.session_state.show_assistant_input = True

    if st.session_state.show_assistant_input:
        assistant_audio = st.audio_input("🎤 Press to record")
        if assistant_audio is not None:
            with st.spinner("🤔 Thinking..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(assistant_audio.getvalue())
                    tmp_audio_path = tmp_file.name
                try:
                    question = transcribe_audio(tmp_audio_path)
                    if question and not question.startswith("Error"):
                        st.info(f"You asked: {question}")
                        answer, is_emergency = answer_patient_question(question)
                        if is_emergency:
                            st.error("🚨 Emergency! Calling caregiver!")
                        now = datetime.now()
                        answer_audio = text_to_speech(answer, f"temp_answer_{now.timestamp()}.mp3")
                        st.session_state.assistant_response = answer
                        st.session_state.assistant_audio_path = str(answer_audio)
                        st.session_state.show_assistant_input = False
                        st.rerun()
                    else:
                        st.error("Sorry, couldn't hear that clearly.")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    try:
                        os.remove(tmp_audio_path)
                    except:
                        pass
    else:
        if st.session_state.assistant_response:
            st.success("💬 My Answer:")
            st.markdown(f"### {st.session_state.assistant_response}")
            if st.session_state.assistant_audio_path:
                if Path(st.session_state.assistant_audio_path).exists():
                    st.audio(st.session_state.assistant_audio_path, autoplay=True)
                    try:
                        time_module.sleep(1)
                        os.remove(st.session_state.assistant_audio_path)
                    except:
                        pass
            if st.button("🎤 Ask Another Question", use_container_width=True, type="primary"):
                st.session_state.assistant_response = None
                st.session_state.assistant_audio_path = None
                st.session_state.show_assistant_input = True
                st.rerun()
    st.divider()

# ========================================
# RESTORED LIVEKIT EMBEDDED ROOM
# ========================================
if livekit_active:
    st.header("🎙️ Live Recording Session")
    st.info("Your caregiver is monitoring for your safety")

    LIVEKIT_URL = os.getenv("LIVEKIT_URL")

    token_server_running = False
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        token_server_running = response.status_code == 200
    except:
        pass

    if not token_server_running:
        st.warning("⚠️ Token server not running. Cannot connect to room.")
    elif not LIVEKIT_URL:
        st.warning("⚠️ LiveKit not configured.")
    else:
        try:
            response = requests.get("http://localhost:5000/get_token?identity=patient_view", timeout=5)
            token_data = response.json()
            token = token_data["token"]

            meet_url = f"https://meet.livekit.io/custom?liveKitUrl={LIVEKIT_URL}&token={token}"

            st.caption("Click to join the monitoring room (allow microphone when prompted)")

            st.components.v1.iframe(
                src=meet_url,
                height=600,
                scrolling=False
            )
        except Exception as e:
            st.error(f"Unable to connect: {e}")
    st.divider()
# --- END OF RESTORED SECTION ---


# Footer
st.caption("💡 Your caregiver monitors your conversations to keep you safe.")
if livekit_active or assistant_mode:
    st.caption("🔴 Recording active - I'm listening and ready to help.")