# src/summarizer.py
import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# ========================================
# PATIENT SUMMARY

# ========================================

SIMPLE_SUMMARY_PROMPT = """
You are summarizing a conversation for a person with dementia.

**CRITICAL RULES:**
1. **YOU MUST ONLY USE FACTS EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, OR ADD ANY INFORMATION NOT IN THE TRANSCRIPT.**
3. **DO NOT mention people who are not explicitly named in the transcript.**
4. **Use simple, clear language (5th grade level).**
5. **Keep it under 50 words.**
6. **Address the patient directly using "you" (e.g., "You spoke with Sarah").**

**Known People (use ONLY if they appear in transcript):**
{known_people}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate simple summary for patient (FACTS ONLY):**
"""

# ========================================
# CAREGIVER SUMMARY (for dashboard)
# ========================================

CAREGIVER_SUMMARY_PROMPT = """
You are summarizing a conversation for a CAREGIVER monitoring a dementia patient.

**CRITICAL RULES:**
1. **YOU MUST ONLY USE FACTS EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, OR ADD ANY INFORMATION NOT IN THE TRANSCRIPT.**
3. **Write in third person ABOUT the patient (use "patient", "they", "them").**
4. **Use clinical but compassionate language.**
5. **Keep it under 75 words.**
6. **Include relevant behavioral observations.**

**Examples:**
- GOOD: "Patient spoke with their daughter Sarah about upcoming visit. Patient asked about Sarah's children multiple times, showing some repetitive questioning."
- BAD: "You talked to Sarah" (that's for patient, not caregiver)

**Known People (use ONLY if they appear in transcript):**
{known_people}

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate caregiver summary (third person, FACTS ONLY):**
"""

# ========================================
# CLINICAL SUMMARY (NO JSON MODE - parse manually)
# ========================================

CLINICAL_SUMMARY_PROMPT = """
You are a clinical assistant analyzing a conversation with a dementia patient.

**CRITICAL ANTI-HALLUCINATION RULES:**
1. **YOU MUST ONLY USE INFORMATION EXPLICITLY STATED IN THE TRANSCRIPT BELOW.**
2. **DO NOT INVENT, ASSUME, GUESS, OR ADD ANY INFORMATION.**
3. **If information is missing or unclear, explicitly state "Unknown" or "Insufficient data".**
4. **DO NOT infer relationships, events, or details not explicitly mentioned.**
5. **DO NOT mention people who are not named in the transcript.**

**THE TRANSCRIPT (your ONLY source of truth):**
{transcript}

**Generate clinical summary in this EXACT format (one per line):**

PARTICIPANT: [Name if mentioned, otherwise "Patient speaking alone"]
TOPICS: [Comma-separated list of topics, or "Unclear recording"]
MOOD: [positive, neutral, anxious, confused, or unknown]
COGNITIVE_STATE: [One sentence observation, or "Insufficient data"]
CONCERNS: [Comma-separated concerns, or "None"]

**IMPORTANT: Follow the format exactly. Do not add extra text.**
"""


# ========================================
# SUMMARIZATION FUNCTIONS
# ========================================

def summarize_transcript_simple(transcript: str) -> str:
    """Generate simple patient-facing summary"""
    if not client:
        return "Error: OpenAI client not initialized."
    if not transcript or len(transcript.strip()) < 10:
        return "The recording was too short or unclear."

    print("🧠 Generating patient summary...")

    try:
        people = get_all_people()
        if not people:
            formatted_people = "No people profiles available."
        else:
            formatted_people = "\n".join(
                [f"- {p.get('name')} ({p.get('relationship')})" for p in people]
            )
    except Exception as e:
        print(f"Warning: Could not fetch people list. {e}")
        formatted_people = "Error fetching people list."

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": SIMPLE_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people
                    )
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        summary = completion.choices[0].message.content.strip()

        if len(summary) > 200:
            print("⚠️ Summary too long, truncating.")
            summary = summary[:197] + "..."

        print("✅ Patient summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during patient summarization: {e}")
        return "Error creating summary."


def summarize_transcript_caregiver(transcript: str) -> str:
    """Generate caregiver-facing summary (third person)"""
    if not client:
        return "Error: OpenAI client not initialized."
    if not transcript or len(transcript.strip()) < 10:
        return "Recording too short or unclear to analyze."

    print("🩺 Generating caregiver summary...")

    try:
        people = get_all_people()
        if not people:
            formatted_people = "No people profiles available."
        else:
            formatted_people = "\n".join(
                [f"- {p.get('name')} ({p.get('relationship')})" for p in people]
            )
    except Exception as e:
        print(f"Warning: Could not fetch people list. {e}")
        formatted_people = "Error fetching people list."

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": CAREGIVER_SUMMARY_PROMPT.format(
                        transcript=transcript,
                        known_people=formatted_people
                    )
                }
            ],
            temperature=0.1,
            max_tokens=150
        )
        summary = completion.choices[0].message.content.strip()

        if len(summary) > 300:
            print("⚠️ Caregiver summary too long, truncating.")
            summary = summary[:297] + "..."

        print("✅ Caregiver summary complete!")
        return summary

    except Exception as e:
        print(f"❌ Error during caregiver summarization: {e}")
        return "Error creating caregiver summary."


def summarize_transcript_clinical(transcript: str) -> dict:
    """Generate clinical summary WITHOUT json_object mode"""
    if not client:
        return {"error": "OpenAI client not initialized."}
    if not transcript or len(transcript.strip()) < 10:
        return {
            "participant": "Patient speaking alone",
            "topics_discussed": ["Recording too short"],
            "patient_mood": "unknown",
            "cognitive_state": "Insufficient data - recording too brief",
            "key_concerns": []
        }

    print("🩺 Generating clinical summary...")

    prompt_content = CLINICAL_SUMMARY_PROMPT.format(transcript=transcript)

    try:
        # Use regular text completion instead of JSON mode
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt_content}
            ],
            temperature=0.1,
            max_tokens=300
        )

        response_text = completion.choices[0].message.content.strip()

        # Parse the structured text response manually
        clinical_data = {
            "participant": "Unknown",
            "topics_discussed": ["Unclear"],
            "patient_mood": "unknown",
            "cognitive_state": "Unknown",
            "key_concerns": []
        }

        # Parse line by line
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PARTICIPANT:'):
                clinical_data["participant"] = line.replace('PARTICIPANT:', '').strip()
            elif line.startswith('TOPICS:'):
                topics_str = line.replace('TOPICS:', '').strip()
                if topics_str and topics_str.lower() != 'unclear recording':
                    clinical_data["topics_discussed"] = [t.strip() for t in topics_str.split(',')]
                else:
                    clinical_data["topics_discussed"] = ["Unclear recording"]
            elif line.startswith('MOOD:'):
                clinical_data["patient_mood"] = line.replace('MOOD:', '').strip().lower()
            elif line.startswith('COGNITIVE_STATE:'):
                clinical_data["cognitive_state"] = line.replace('COGNITIVE_STATE:', '').strip()
            elif line.startswith('CONCERNS:'):
                concerns_str = line.replace('CONCERNS:', '').strip()
                if concerns_str and concerns_str.lower() != 'none':
                    clinical_data["key_concerns"] = [c.strip() for c in concerns_str.split(',')]

        print("✅ Clinical summary complete!")
        return clinical_data

    except Exception as e:
        print(f"❌ Error in clinical summarization:")
        traceback.print_exc()

        return {
            "participant": "Error",
            "topics_discussed": ["Error processing"],
            "patient_mood": "unknown",
            "cognitive_state": f"Error in summarization: {e}",
            "key_concerns": ["Error processing transcript"]
        }