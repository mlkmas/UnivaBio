# pages/3_Admin_Tools.py
import streamlit as st
from datetime import datetime, time, date, timedelta
from src.schemas import Medication, PersonProfile
from src.database import (
    add_medication, get_all_medications, update_medication,
    delete_medication, add_person, get_all_people, delete_person, update_person,
    get_settings, update_settings
)
from pathlib import Path
import face_recognition
import requests

if 'page_loaded_admin' not in st.session_state:
    st.session_state.page_loaded_admin = True
    st.session_state.show_med_dialog = False
    st.session_state.show_person_dialog = False

st.set_page_config(page_title="Admin Tools", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .settings-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-active {
        background: #10b981;
    }
    .status-inactive {
        background: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Admin & Caregiver Tools")
st.caption("Control all system settings from here")
st.divider()

# Initialize session states
if 'show_med_dialog' not in st.session_state:
    st.session_state.show_med_dialog = False
if 'show_person_dialog' not in st.session_state:
    st.session_state.show_person_dialog = False
if 'editing_med_id' not in st.session_state:
    st.session_state.editing_med_id = None
if 'editing_med_data' not in st.session_state:
    st.session_state.editing_med_data = None


def open_med_dialog(med_id=None, med_data=None):
    st.session_state.show_med_dialog = True
    st.session_state.show_person_dialog = False
    st.session_state.editing_med_id = med_id
    st.session_state.editing_med_data = med_data


def close_med_dialog():
    st.session_state.show_med_dialog = False
    st.session_state.editing_med_id = None
    st.session_state.editing_med_data = None


def open_person_dialog():
    st.session_state.show_person_dialog = True
    st.session_state.show_med_dialog = False


def close_person_dialog():
    st.session_state.show_person_dialog = False


# ========================================
# SYSTEM SETTINGS AT TOP
# ========================================
st.markdown("### ⚙️ System Settings")

settings = get_settings()

# Settings in 2 columns side by side
col_settings1, col_settings2 = st.columns(2)

# LEFT: Daily Recap Settings
with col_settings1:
    with st.container(border=True):
        st.markdown("**📅 Daily Recap Settings**")

        recap_enabled = st.toggle(
            "Enable Automatic Daily Recap",
            value=settings.get('daily_recap_enabled', True),
            key="recap_enabled_toggle"
        )

        recap_time_str = settings.get('daily_recap_time', '19:00')
        try:
            recap_hour, recap_minute = map(int, recap_time_str.split(':'))
            default_recap_time = time(recap_hour, recap_minute)
        except:
            default_recap_time = time(19, 0)

        recap_time = st.time_input(
            "Recap Time (Israel Time)",
            value=default_recap_time,
            help="Time when daily recap will automatically play"
        )

        if st.button("💾 Save Recap Settings", use_container_width=True):
            update_settings({
                'daily_recap_enabled': recap_enabled,
                'daily_recap_time': recap_time.strftime('%H:%M')
            })
            st.success("✅ Recap settings saved!")
            st.rerun()

# RIGHT: Recording Control
with col_settings2:
    with st.container(border=True):
        st.markdown("**🔴 Continuous Recording**")

        # Check if services are running
        token_server_running = False
        try:
            response = requests.get("http://localhost:5000/health", timeout=2)
            token_server_running = response.status_code == 200
        except:
            pass

        status_class = "status-active" if token_server_running else "status-inactive"
        status_text = "Online" if token_server_running else "Offline"
        st.markdown(f'<span class="status-indicator {status_class}"></span>Token Server: {status_text}',
                    unsafe_allow_html=True)

        if not token_server_running:
            st.warning("⚠️ Token server must be running")
            st.code("poetry run python src/token_server.py", language="bash")
        else:
            livekit_active = settings.get('livekit_session_active', False)

            col_start, col_stop = st.columns(2)

            with col_start:
                if st.button("🟢 Start Recording", use_container_width=True,
                             disabled=livekit_active, type="primary"):
                    update_settings({'livekit_session_active': True})
                    st.success("✅ Recording started!")
                    st.rerun()

            with col_stop:
                if st.button("🔴 Stop Recording", use_container_width=True,
                             disabled=not livekit_active):
                    update_settings({'livekit_session_active': False})
                    st.success("✅ Recording stopped")
                    st.rerun()

st.divider()

# ========================================
# MEDICATIONS & PEOPLE SIDE BY SIDE
# ========================================

col1, col2 = st.columns([1, 1], gap="large")

# LEFT COLUMN: MEDICATIONS
with col1:
    st.markdown("### 💊 Medications")

    # Header with Add button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col2:
        if st.button("➕ Add", key="add_med_btn", use_container_width=True, type="primary"):
            open_med_dialog()
            st.rerun()

    medications = get_all_medications()

    if not medications:
        st.info("📭 No medications yet")
    else:
        for idx, med in enumerate(medications):
            med_id = str(med.get('_id') or med.get('id'))

            with st.container(border=True):
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 12px; border-radius: 8px; margin-bottom: 10px;'>
                    <div style='color: white; font-weight: 600;'>⏰ {med.get('time_to_take', 'N/A')}</div>
                    <div style='color: white; font-size: 18px; margin-top: 4px;'>{med.get('name', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

                info_col, btn_col = st.columns([3, 1])

                with info_col:
                    st.caption(f"💊 {med.get('dosage', 'N/A')}")
                    st.caption(f"🎯 {med.get('purpose', 'N/A')}")

                with btn_col:
                    if st.button("✏️", key=f"edit_med_{med_id}", use_container_width=True):
                        open_med_dialog(med_id, med)
                        st.rerun()
                    if st.button("🗑️", key=f"del_med_{med_id}", use_container_width=True):
                        delete_medication(med_id)
                        st.rerun()

# RIGHT COLUMN: PEOPLE
with col2:
    st.markdown("### 👥 People")

    # Header with Add button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col2:
        if st.button("➕ Add", key="add_person_btn", use_container_width=True, type="primary"):
            open_person_dialog()
            st.rerun()

    people = get_all_people()

    if not people:
        st.info("📭 No people profiles yet")
    else:
        for person in people:
            person_id = str(person.get('_id') or person.get('id'))

            with st.container(border=True):
                p_img_col, p_info_col, p_btn_col = st.columns([1, 3, 1])

                with p_img_col:
                    photo_path = person.get('photo_url', 'https://via.placeholder.com/150')
                    if Path(photo_path).is_file():
                        st.image(photo_path, width=70)
                    else:
                        st.image('https://via.placeholder.com/150', width=70)

                with p_info_col:
                    st.markdown(f"**{person.get('name')}**")
                    st.caption(f"👤 {person.get('relationship')}")

                with p_btn_col:
                    if st.button("🗑️", key=f"del_person_{person_id}", use_container_width=True):
                        delete_person(person_id)
                        st.rerun()


# ========================================
# DIALOGS
# ========================================
@st.dialog("💊 Medication", width="small")
def medication_dialog():
    is_editing = st.session_state.editing_med_id is not None
    med_data = st.session_state.editing_med_data or {}

    st.markdown(f"**{'Edit' if is_editing else 'Add'} Medication**")

    med_name = st.text_input("Name", value=med_data.get('name', ''))

    col_dose, col_time = st.columns(2)
    with col_dose:
        med_dosage = st.text_input("Dosage", value=med_data.get('dosage', ''))
    with col_time:
        default_time = time(8, 0)
        if is_editing and med_data.get('time_to_take'):
            try:
                default_time = datetime.strptime(med_data['time_to_take'], '%I:%M %p').time()
            except:
                pass
        med_time = st.time_input("Time (Israel Time)", value=default_time, step=timedelta(minutes=15))

    med_purpose = st.text_input("Purpose", value=med_data.get('purpose', ''))

    schedule_options = ["Daily", "Weekly", "One-Time"]
    current_schedule = med_data.get('schedule_type', 'Daily')
    schedule_index = schedule_options.index(current_schedule) if current_schedule in schedule_options else 0
    schedule_type = st.selectbox("Schedule", options=schedule_options, index=schedule_index)

    days_of_week = None
    specific_date = None

    if schedule_type == 'Weekly':
        days_of_week = st.multiselect(
            "Days",
            options=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=[d[:3] for d in med_data.get('days_of_week', [])]
        )
        day_map = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
                   "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
        days_of_week = [day_map[d] for d in days_of_week]

    elif schedule_type == 'One-Time':
        default_date = date.today()
        if is_editing and med_data.get('specific_date'):
            if isinstance(med_data['specific_date'], datetime):
                default_date = med_data['specific_date'].date()
        specific_date = st.date_input("Date", value=default_date)

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Save", type="primary", use_container_width=True):
            if not all([med_name, med_dosage, med_purpose]):
                st.error("Please fill all fields")
                st.stop()

            time_str = med_time.strftime("%I:%M %p")
            final_specific_date = None

            if schedule_type == 'One-Time' and specific_date:
                final_specific_date = datetime.combine(specific_date, time(0, 0))

            med_dict = {
                "name": med_name,
                "dosage": med_dosage,
                "purpose": med_purpose,
                "time_to_take": time_str,
                "schedule_type": schedule_type,
                "days_of_week": days_of_week if schedule_type == 'Weekly' else None,
                "specific_date": final_specific_date
            }

            try:
                if is_editing:
                    update_medication(st.session_state.editing_med_id, med_dict)
                    st.success("✅ Updated!")
                else:
                    new_med = Medication(**med_dict)
                    add_medication(new_med)
                    st.success("✅ Added!")

                close_med_dialog()
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            close_med_dialog()
            st.rerun()


@st.dialog("👤 Person Profile", width="small")
def person_dialog():
    st.markdown("**Add Person Profile**")

    person_name = st.text_input("Name")
    person_relationship = st.text_input("Relationship")
    person_notes = st.text_area("Notes (optional)", height=80)
    uploaded_photo = st.file_uploader("Photo", type=["jpg", "png", "jpeg"])

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Add", type="primary", use_container_width=True):
            if not person_name or not person_relationship:
                st.error("Name and relationship required")
                st.stop()

            photo_url_to_save = "https://via.placeholder.com/150"
            face_encoding_list = None

            if uploaded_photo is not None:
                try:
                    image_dir = Path("images")
                    image_dir.mkdir(parents=True, exist_ok=True)

                    safe_filename = f"{person_name.lower().replace(' ', '_')}_{uploaded_photo.name}"
                    file_path = image_dir / safe_filename

                    with open(file_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())
                    photo_url_to_save = str(file_path)

                    with st.spinner("Analyzing face..."):
                        image = face_recognition.load_image_file(file_path)
                        encodings = face_recognition.face_encodings(image)

                        if encodings:
                            face_encoding_list = encodings[0].tolist()
                            st.success("✅ Face detected!")
                        else:
                            st.warning("⚠️ No face found")

                except Exception as e:
                    st.error(f"Photo error: {e}")

            try:
                new_person = PersonProfile(
                    name=person_name,
                    relationship=person_relationship,
                    photo_url=photo_url_to_save,
                    notes=person_notes
                )

                person_id = add_person(new_person)

                if person_id and face_encoding_list:
                    update_person(person_id, {"face_encoding": face_encoding_list})

                st.success(f"✅ Added {person_name}!")
                close_person_dialog()
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            close_person_dialog()
            st.rerun()


if st.session_state.show_med_dialog:
    medication_dialog()

if st.session_state.show_person_dialog:
    person_dialog()