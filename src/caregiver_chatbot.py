# src/caregiver_chatbot.py
from openai import OpenAI
from dotenv import load_dotenv
from src.database import get_recent_conversations, get_all_people

load_dotenv()

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None


def answer_caregiver_question(question: str, days_back: int = 7) -> str:
    if not client:
        return "Error: OpenAI client not initialized."

    print(f"🤔 Caregiver asked: {question}")

    conversations = get_recent_conversations(days=days_back)

    if not conversations:
        return f"I don't have any conversation records from the last {days_back} days. Try running 'poetry run python populate_mock_data.py' to create some."

    # --- FIX 1: Limit the number of conversations sent to the AI ---
    # This prevents the "Request too large" error.
    if len(conversations) > 30:
        print(f"⚠️  Context too large ({len(conversations)} conversations). Limiting to most recent 30.")
        conversations = conversations[:30] # Keep only the 30 most recent

    conversation_texts = []
    for i, conv in enumerate(conversations, 1):
        date = conv.get('generated_at', '').strftime('%A, %B %d at %I:%M %p') if conv.get('generated_at') else 'Unknown'
        summary = conv.get('caregiver_summary', conv.get('simple_summary', 'No summary'))
        mood = conv.get('patient_mood', 'unknown')
        concerns = conv.get('key_concerns', [])

        conv_text = f"""Conversation {i} - {date}:
- Summary: {summary}
- Patient Mood: {mood}
- Concerns: {', '.join(concerns) if concerns else 'None'}"""
        conversation_texts.append(conv_text)

    context = "\n".join(conversation_texts)

    try:
        people = get_all_people()
        people_context = "\n".join([
            f"- {p.get('name')} ({p.get('relationship')})"
            for p in people
        ]) if people else "No people profiles."
    except:
        people_context = "Error loading people."

    prompt = f"""You are a helpful AI assistant for a caregiver.
Answer the caregiver's question based ONLY on the data provided.

**CRITICAL RULES FOR ANSWERING:**
1.  **Synthesize and Summarize:** DO NOT list every single conversation (e.g., "Conversation 1, Conversation 2...").
2.  **Group Information:** If asked for concerns, summarize the *types* of concerns (e.g., "The patient frequently expressed physical pain and showed confusion about time.").
3.  **Be Concise:** Keep your answer to a few clear sentences.
4.  **If you don't know, say so:** If the information isn't in the context, say "I do not have information about that."

**Recent Conversations Data:**
{context}

**Known People Data:**
{people_context}

**Caregiver's Question:** {question}

**Your Concise Answer:**
"""

    try:
        completion = client.chat.completions.create(
            # --- FIX 2: Use gpt-3.5-turbo ---
            # It's faster, cheaper, and will prevent rate limit issues.
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        answer = completion.choices[0].message.content.strip()
        print(f"✅ Answer generated")
        return answer
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Error generating answer: {e}"