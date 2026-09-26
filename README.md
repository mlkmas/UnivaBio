# RememberMe AI

**Ambient memory support for people living with dementia.**

Submitted to [UnivaBio 2026](https://univabio.devpost.com/) (theme: Artificial Intelligence for Human Health).

---

## The problem

Most memory aids assume the patient will open an app and ask for help. Dementia
takes away exactly that behaviour. As people become aware of their memory loss,
many withdraw: they stop asking questions to hide the forgetting, and stop
mentioning pain, confusion or fear. The people who need the most help are the
least likely to ask for it, and caregivers often find out about a problem only
after a crisis.

More than 55 million people live with dementia worldwide, and most of them are
cared for at home by family ([WHO](https://www.who.int/news-room/fact-sheets/detail/dementia)).

## The idea

RememberMe AI does not wait to be asked. It listens to the conversations already
happening in the home and turns them into memory the patient can get back: a
spoken recap of the day, answers to "who came today?", and medication reminders
that connect to what the patient actually said. The caregiver gets a clear
record of each day without having been in the room.

---

## What works today

Everything below runs in the Streamlit prototype in this repository.

| Feature | What it does |
|---|---|
| **Conversation capture** | A LiveKit room streams audio; each segment is transcribed with Whisper and stored in MongoDB. |
| **One transcript, three summaries** | Every conversation produces a short second-person recap for the patient, a behavioural summary for the caregiver, and a structured observation log (participant, topics, mood, key concerns). |
| **Spoken daily recap** | At a time the caregiver sets, the day is summarised and read aloud with text-to-speech. |
| **Context-grounded medication reminders** | A background scheduler fires reminders at the prescribed times. If the patient mentioned a matching symptom earlier (for example knee pain), the reminder refers to it. |
| **Patient assistant** | The patient presses one button and speaks a question. The answer comes from that day's conversations and the caregiver-entered people and medications, and is read back aloud. |
| **Emergency keywords** | Phrases such as "chest pain" or "fell down" in a patient question show an on-screen emergency message. See *Limitations* below. |
| **Who is this?** | The patient takes a photo of a visitor; face recognition matches it against people the caregiver has enrolled and shows their name and relationship. |
| **Caregiver dashboard** | Calendar with a daily mood indicator, a timeline of every conversation with all three summaries, and a chatbot that answers questions about the patient's recent history. |
| **Admin tools** | Caregivers manage medications, people profiles and photos, recap time, and recording sessions. |

---

## Safety by design

**Nothing is inferred.** Every prompt that produces a summary, recap or reminder
is restricted to facts stated in the transcript. The system is told never to
invent a visitor, symptom or event, and the observation log records "Unknown"
when information is missing. For someone who cannot check an answer against their own memory, a
plausible fabrication is worse than no answer.

**The patient's words never change the care plan.** Confabulation and
repetition are symptoms. The system reads medications but never edits them;
only a caregiver can add or change a medication, in Admin Tools.

**Support tool, not a medical device.** It makes no diagnosis and gives no
treatment advice. The observation log is meant to help a caregiver or clinician
notice patterns, not to replace their judgement.

**Privacy.** Audio is captured only while a recording session is running, and
recordings are gitignored and kept local. Face profiles are enrolled by the
caregiver, not collected automatically. A real deployment would need consent
from the patient (or their legal representative) and from regular visitors;
see *What's next*.

---

## Architecture

```
Conversation in the home (LiveKit room)
        ↓
Transcription (Whisper)
        ↓
Three-view summarisation (GPT-4)  →  patient / caregiver / observation log
        ↓
Care record (MongoDB)
        ↓
Daily recap · Medication reminder · Patient Q&A · Visitor ID
        ↓
Speech output (OpenAI TTS)
```

| Layer | Technology |
|---|---|
| App | Streamlit (multipage) |
| Data | MongoDB Atlas, Pydantic models |
| Real-time audio | LiveKit, Flask token server |
| Transcription | OpenAI Whisper |
| Language models | GPT-4 (summaries, patient Q&A), GPT-3.5 Turbo (recap, reminders, caregiver chatbot) |
| Speech | OpenAI TTS |
| Vision | `face_recognition` (dlib) |

### Project layout

```
app.py                       Streamlit entry point
pages/
  1_Caregiver_Dashboard.py   calendar, timeline, mood, history chatbot
  2_Patient_View.py          recap, reminders, voice assistant
  3_Admin_Tools.py           medications, people, settings, recording
  4_Who_Is_This.py           visitor identification
src/
  livekit_client.py          joins the room, captures and processes audio
  token_server.py            issues LiveKit access tokens
  transcriber.py             speech to text
  summarizer.py              three-view summarisation
  recap_generator.py         daily recap
  smart_reminder.py          context-grounded medication reminders
  patient_assistant.py       patient Q&A and emergency keywords
  caregiver_chatbot.py       caregiver Q&A over history
  background_scheduler.py    fires reminders and the daily recap
  text_to_speech.py          spoken output
  database.py                MongoDB access layer
  schemas.py                 Pydantic models
populate_mock_data.py        fills the database with a month of sample history
```

---

## Running it

Requires Python 3.11+, a MongoDB Atlas cluster, an OpenAI API key, and (for
live capture) a free LiveKit Cloud project.

```bash
git clone https://github.com/mlkmas/UnivaBio.git
cd UnivaBio
poetry install
poetry run pip install faker        # only needed for sample data
```

`face-recognition` depends on `dlib`, which needs CMake and a C++ compiler (on
Windows, install Visual Studio Build Tools first). Every page except *Who Is
This?* works without it.

Copy `.env.example` to `.env` and fill in `MONGO_CONNECTION_STRING`,
`OPENAI_API_KEY`, `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.

```bash
python populate_mock_data.py        # optional: a month of sample history, no API calls
streamlit run app.py
```

For live capture, reminders and the automatic recap, run these alongside the
app, each in its own terminal:

```bash
python src/token_server.py          # LiveKit tokens on port 5000
python src/livekit_client.py        # listens in the room and processes audio
python src/background_scheduler.py  # medication reminders and daily recap
```

---

## Limitations

Stated plainly, because they matter in a care setting:

- **Emergency alerts stay on screen.** The patient sees an emergency message,
  but no notification is sent to the caregiver yet. Keyword matching is also
  simple and can produce false positives.
- **Speaker identity comes from the LiveKit participant name** ("patient" or
  "caregiver"), not from voice recognition.
- **English only** in the current prompts.
- **Not tested with patients or caregivers.** All sample data is synthetic.

## What's next

- Caregiver notifications for emergencies (dashboard alert first, then SMS or push)
- Participation tracking over time, so a decline in how much the patient speaks
  shows up as a trend rather than a feeling
- A consent flow for the patient, their representative and regular visitors,
  with automatic deletion of raw audio after transcription
- Multilingual support, starting with Arabic and Hebrew
- A FastAPI and React rebuild with a voice-first patient interface
- Testing with real caregivers

---


## References

- World Health Organization. [Dementia fact sheet](https://www.who.int/news-room/fact-sheets/detail/dementia).
- Livingston G, et al. Dementia prevention, intervention, and care: 2024 report of the *Lancet* standing Commission. *The Lancet* 2024; 404(10452): 572–628.
- Woods B, et al. Reminiscence therapy for dementia. *Cochrane Database of Systematic Reviews* 2018, Issue 3, CD001120.

## Author

Malak Masarwe · [github.com/mlkmas](https://github.com/mlkmas)
