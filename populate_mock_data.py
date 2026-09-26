# populate_mock_data.py
import os
import random
from datetime import datetime, timedelta, time
from faker import Faker

# --- Important: Ensure correct imports from your project ---
try:
    # --- MODIFIED: Added client and collection names for optional clearing ---
    from src.database import save_conversation, add_medication, client, db
    from src.database import SEGMENT_COLLECTION, SUMMARY_COLLECTION
    from src.schemas import ConversationSegment, ConversationSummary, Medication
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure this script is run from your main project directory or adjust import paths.")
    exit()
# --- End Imports ---


fake = Faker()

# --- Configuration ---
# --- MODIFIED: Changed from 7 to 32 to cover Nov 1, Nov 2, and all of October ---
NUM_DAYS = 32
MIN_CONVOS_PER_DAY = 2
MAX_CONVOS_PER_DAY = 6

# --- Realistic Mock Data Options ---
PARTICIPANTS = ["Sarah (Daughter)", "Dr. John (Doctor)", "Maria (Caregiver)", "Ahmed (Son)", "Neighbor",
                "Patient speaking alone"]
TOPICS = ["Family update", "Health check", "Daily routine", "Watching TV", "Weather", "Past memories",
          "Appointment scheduling", "Meal discussion"]
MOODS = ["positive", "neutral", "anxious", "confused", "negative", "agitated"]
COG_STATES = ["Clear and engaged", "Slightly forgetful", "Repeated questions", "Confused about time", "Distracted",
              "Well-oriented"]
CONCERNS = ["Repeated a question", "Expressed physical pain", "Showed confusion about time/place", "Memory lapse noted",
            "Seemed anxious", "Frustration expressed", "None"]


def generate_mock_data(num_days: int):
    """Generates and saves mock conversation data for the specified number of past days."""
    if not client:
        print("❌ Cannot generate data: No database connection.")
        return

    print(f"Generating mock data for the past {num_days} days...")
    today = datetime.now().date()

    for i in range(num_days):
        current_date = today - timedelta(days=i)
        num_convos = random.randint(MIN_CONVOS_PER_DAY, MAX_CONVOS_PER_DAY)
        print(f"  Generating {num_convos} conversations for {current_date.strftime('%Y-%m-%d')}...")

        for j in range(num_convos):
            # Generate random times within the day
            conv_start_dt = fake.date_time_between(
                start_date=datetime.combine(current_date, time(6, 0)),
                end_date=datetime.combine(current_date, time(21, 0))
            )
            conv_end_dt = conv_start_dt + timedelta(minutes=random.randint(2, 15))
            summary_gen_dt = conv_end_dt + timedelta(seconds=random.randint(5, 60))

            # Generate fake content
            participant = random.choice(PARTICIPANTS)
            convo_topics = random.sample(TOPICS, k=random.randint(1, 3))  # 1-3 topics
            fake_transcript = f"Fake conversation with {participant}. Discussed {', '.join(convo_topics)}. {fake.paragraph(nb_sentences=random.randint(3, 7))}"
            simple_summary = f"You spoke with {participant} about {', '.join(convo_topics)}. {fake.sentence()}"

            # --- MODIFIED: Added caregiver summary ---
            caregiver_summary = f"Patient spoke with {participant} about {', '.join(convo_topics)}. Patient seemed {random.choice(MOODS)}."

            mood = random.choice(MOODS)
            cog_state = random.choice(COG_STATES)
            num_concerns = 0 if mood == "positive" and cog_state == "Clear and engaged" else random.randint(0, 2)
            key_concerns = random.sample([c for c in CONCERNS if c != "None"],
                                         k=num_concerns)  # Pick 0-2 actual concerns
            if not key_concerns:
                key_concerns = ["None"]  # Ensure 'None' if no specific concerns picked

            try:
                # Create Pydantic Objects
                segment = ConversationSegment(
                    start_time=conv_start_dt,
                    end_time=conv_end_dt,
                    transcript=fake_transcript
                )

                summary = ConversationSummary(
                    segment_id=str(segment.id),  # Use the generated ID
                    generated_at=summary_gen_dt,
                    simple_summary=simple_summary,
                    caregiver_summary=caregiver_summary,  # Added field
                    participant=participant,
                    topics_discussed=convo_topics,
                    patient_mood=mood,
                    cognitive_state=cog_state,
                    key_concerns=key_concerns
                )

                # Save to database
                save_conversation(segment, summary)

            except Exception as e:
                print(f"    ❌ Error creating/saving conversation {j + 1} for {current_date}: {e}")

    print(f"✅ Mock data generation complete for {num_days} days.")


if __name__ == "__main__":
    # --- Optional: Clear existing data ---
    # print("Clearing existing conversation and summary data...")
    # try:
    #     if client:
    #         db[SEGMENT_COLLECTION].delete_many({})
    #         db[SUMMARY_COLLECTION].delete_many({})
    #         print("  Existing data cleared.")
    #     else:
    #         print("  Skipping clear: No database connection.")
    # except Exception as e:
    #     print(f"  Error clearing data: {e}")
    # --- End Optional Clear ---

    generate_mock_data(NUM_DAYS)