# add_today.py
"""
One-time script to add 4 specific conversations for the demo on Nov 6, 2025
"""
from datetime import datetime, time
from src.database import save_conversation
from src.schemas import ConversationSegment, ConversationSummary
import os

print("=" * 70)
print("🚀 ADDING 4 DEMO CONVERSATIONS FOR TODAY...")
print("=" * 70)

# We are hard-coding today's date for the demo
# (Based on the established current time of Thursday, Nov 6, 2025)
today = datetime(2025, 11, 6)

# --- 1. Andy's Visit + Appointment ---
try:
    conv_time_1 = datetime.combine(today, time(9, 5, 0))  # 9:05 AM

    transcript_1 = "Patient: Andy! It's so good to see you. Andy: You too! How are you feeling? Patient: Oh, you know. Andy: Well, I wanted to let you know I scheduled that doctor's appointment for you. It's for next Tuesday. Patient: Oh, that's wonderful. Thank you."

    segment_1 = ConversationSegment(
        start_time=conv_time_1,
        end_time=conv_time_1,
        transcript=transcript_1,
        speaker_identity="Andy (Neighbor)"  # Assuming Andy is a neighbor
    )

    summary_1 = ConversationSummary(
        segment_id=str(segment_1.id),
        generated_at=conv_time_1,
        simple_summary="You had a nice visit with Andy this morning. He helped you schedule your doctor's appointment for next week.",
        caregiver_summary="Patient had a positive visit with Andy (neighbor). Andy confirmed he scheduled the doctor's appointment for next week. Patient mood was positive.",
        participant="Andy (Neighbor)",
        topics_discussed=["Visitor", "Appointment Scheduling", "Family"],
        patient_mood="positive",
        cognitive_state="Clear and engaged",
        key_concerns=["None"]
    )
    save_conversation(segment_1, summary_1)
    print("✅ 1. Added: Andy's Visit + Appointment")

except Exception as e:
    print(f"❌ Error adding conversation 1: {e}")

# --- 2. Back Pain + Repetitive Question ---
try:
    conv_time_2 = datetime.combine(today, time(10, 30, 0))  # 10:30 AM

    transcript_2 = "Patient: My back is really hurting. Maria: I'm sorry to hear that. Patient: Did I take my medicine? Maria: Not yet, it's not time. Patient: Oh. My back hurts. Maria: I know. Patient: Did I take my medicine? Maria: Not yet, dear. Patient: Did I take my medicine? Maria: No. Patient: Did I take my medicine? Maria: No. Patient: Did I take my medicine? Maria: No. Patient: Did I take my medicine? Maria: No, it's not time."

    segment_2 = ConversationSegment(
        start_time=conv_time_2,
        end_time=conv_time_2,
        transcript=transcript_2,
        speaker_identity="Maria (Caregiver)"
    )

    summary_2 = ConversationSummary(
        segment_id=str(segment_2.id),
        generated_at=conv_time_2,
        simple_summary="You spoke with Maria and mentioned your back was hurting. You asked a few times if you had taken your medicine.",
        caregiver_summary="Patient complained of significant back pain. They asked 'Did I take my medicine?' 6 times in one conversation, showing severe repetitive questioning. Mood was anxious.",
        participant="Maria (Caregiver)",
        topics_discussed=["Health Complaint", "Pain", "Medication", "Repetitive Questioning"],
        patient_mood="anxious",
        cognitive_state="Confused, repetitive questioning",
        key_concerns=["Expressed physical pain", "Repetitive questioning (6 times)"]
    )
    save_conversation(segment_2, summary_2)
    print("✅ 2. Added: Back Pain + Repetitive Question")

except Exception as e:
    print(f"❌ Error adding conversation 2: {e}")

# --- 3. Tripping on Door Stamp (Fall Risk) ---
try:
    conv_time_3 = datetime.combine(today, time(11, 15, 0))  # 11:15 AM

    transcript_3 = "Whoops! Oh, that stupid step. I almost fell again. This door stamp is dangerous. I keep tripping on it. Someone needs to fix that."

    segment_3 = ConversationSegment(
        start_time=conv_time_3,
        end_time=conv_time_3,
        transcript=transcript_3,
        speaker_identity="Patient speaking alone"
    )

    summary_3 = ConversationSummary(
        segment_id=str(segment_3.id),
        generated_at=conv_time_3,
        simple_summary="You almost tripped on the doorstep. You noted that it's dangerous and you should be careful.",
        caregiver_summary="Patient was recorded speaking alone after almost tripping. They explicitly mentioned the 'door stamp' (doorstep/threshold) is dangerous and that they 'keep tripping on it'. This is a clear fall risk.",
        participant="Patient speaking alone",
        topics_discussed=["Safety Hazard", "Fall Risk", "Home Environment"],
        patient_mood="agitated",
        cognitive_state="Aware of hazard",
        key_concerns=["Fall risk", "Tripped on doorstep", "Agitation"]
    )
    save_conversation(segment_3, summary_3)
    print("✅ 3. Added: Door Stamp Fall Risk")

except Exception as e:
    print(f"❌ Error adding conversation 3: {e}")

# --- 4. Skipped Lunch ---
try:
    conv_time_4 = datetime.combine(today, time(12, 40, 0))  # 12:40 PM

    transcript_4 = "Maria: It's time for lunch, I made you a nice sandwich. Patient: I'm not hungry. I don't want to eat. Maria: Please, you should eat something. Patient: No. I'm going to my room. Just leave me be."

    segment_4 = ConversationSegment(
        start_time=conv_time_4,
        end_time=conv_time_4,
        transcript=transcript_4,
        speaker_identity="Maria (Caregiver)"
    )

    summary_4 = ConversationSummary(
        segment_id=str(segment_4.id),
        generated_at=conv_time_4,
        simple_summary="You spoke with Maria at lunchtime, but you weren't feeling very hungry and didn't want to eat.",
        caregiver_summary="Patient refused to eat lunch when offered by caregiver (Maria). Stated they were not hungry and retreated to their room. Patient skipped lunch.",
        participant="Maria (Caregiver)",
        topics_discussed=["Meal Discussion", "Refusal of Food", "Apathy"],
        patient_mood="negative",
        cognitive_state="Withdrawn",
        key_concerns=["Skipped lunch", "Refused food", "Negative mood"]
    )
    save_conversation(segment_4, summary_4)
    print("✅ 4. Added: Skipped Lunch")

except Exception as e:
    print(f"❌ Error adding conversation 4: {e}")

print("\n" + "=" * 70)
print("✅ DONE. All 4 demo conversations are in the database.")
print("   Go to the Caregiver Dashboard to see them!")
print("=" * 70)