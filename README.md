# RememberMe AI

**Ambient memory support for people living with dementia.**

Most memory aids assume the patient will open an app and ask for help. Dementia
removes exactly that behaviour. As people become aware of their memory loss they
often withdraw — they stop asking questions to hide the forgetting, and stop
reporting pain, confusion, and fear. The people who need the most help are the
least likely to request it, and caregivers frequently learn of a problem only
after a crisis.

RememberMe AI takes the opposite approach. It listens to the conversations
already happening in the home and turns them into memory the patient can get
back, without anyone having to start it.

---

## What it does

**Ambient capture.** Conversations are recorded and transcribed automatically.
The patient does not open an app, press a button, or ask a question.

**One transcript, three summaries.** Each conversation produces a simple
second-person recap for the patient, a behavioural summary for the caregiver,
and a structured clinical record capturing mood, cognitive state, topics, and
key concerns.

**Spoken daily recap.** At a configurable time each evening the system reads the
day back aloud: who visited, what was said, what happened.

**Context-grounded medication reminders.** Reminders reference what the patient
actually said. If they mentioned knee pain at breakfast, the afternoon painkiller
reminder says so.

**Patient assistant.** Answers questions like "who came today?" or "did I take my
pills?" from that person's own recorded day, in plain language, with emergency
keyword escalation to the caregiver.

**Visitor identification.** Face recognition against caregiver-enrolled profiles
answers "who is this person?" in real time.

**Caregiver dashboard.** A calendar and timeline of every conversation, mood
trends, and a chatbot that can be asked about the patient's recent history.

---

## Design decisions worth knowing

**Nothing is inferred.** Every summarisation prompt is constrained to facts
present in the transcript. The system will not invent a visitor, a symptom, or an
event. In a care context a plausible-sounding fabrication is worse than no
answer, because the patient has no way to check it.

**The patient's speech is not fully trusted.** Confabulation and repetition are
symptoms, not noise. Anything clinical — medication changes in particular — is
surfaced to the caregiver for confirmation rather than acted on directly.

**This is a support tool, not a medical device.** It makes no diagnosis and gives
no treatment recommendations.

---

## Architecture

```
Ambient conversation
        ↓
   Transcription
        ↓
Tri-view summarisation   →   patient / caregiver / clinical
        ↓
   Care record (MongoDB)
        ↓
Recap · Reminder · Alert · Visitor ID
```

| Layer | Technology |
|---|---|
| App | Streamlit (multipage) |
| Data | MongoDB |
| Real-time audio | LiveKit |
| Transcription | Whisper (or Gemini — see below) |
| Language model | GPT-4 (or Gemini — see below) |
| Speech | OpenAI TTS (or gTTS / edge-tts) |
| Vision | `face_recognition` |
| Validation | Pydantic |

### Project layout

```
app.py                      entry point
pages/
  1_Caregiver_Dashboard.py  timeline, mood trends, history chatbot
  2_Patient_View.py         voice-first patient interface
  3_Admin_Tools.py          settings, medications, people
  4_Who_Is_This.py          visitor identification
src/
  database.py               MongoDB access layer
  schemas.py                Pydantic models
  transcriber.py            speech to text
  summarizer.py             tri-view summarisation
  recap_generator.py        daily spoken recap
  smart_reminder.py         context-grounded medication reminders
  patient_assistant.py      patient-facing Q&A
  caregiver_chatbot.py      caregiver-facing Q&A over history
  text_to_speech.py         spoken output
  livekit_client.py         real-time audio session
  background_scheduler.py   recap and reminder scheduling
```

---

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/mlkmas/rememberMe.git
cd rememberMe
poetry install          # or: pip install -r requirements.txt
```

`face-recognition` needs `dlib`, which needs CMake and a C++ compiler. On
Windows, install Visual Studio Build Tools first. Everything except visitor
identification works without it.

Copy `.env.example` to `.env` and fill it in:

```
MONGO_CONNECTION_STRING=mongodb+srv://user:password@cluster.mongodb.net/
OPENAI_API_KEY=sk-...
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

Verify the connection, then run:

```bash
python verify_setup.py
streamlit run app.py
```

### Demo data

To populate the database with people, medications, and a month of conversation
history without calling any AI API:

```bash
python seed_demo.py --reset
```

---

## Running on Gemini instead of OpenAI

The project can run on Gemini's free tier with no code changes beyond one import
line per module. Drop `src/openai_compat.py` in place, then:

```bash
pip install google-genai gtts
python switch_to_gemini.py
python -m src.openai_compat     # connection check
```

GPT-4 maps to Gemini Flash, Whisper to Gemini's native audio input, and OpenAI
TTS to gTTS. Add `GEMINI_API_KEY` to `.env`. Reverse it with
`python switch_to_gemini.py --undo`.

---

## Status

Working prototype. The Streamlit build in this repository runs end to end. A
FastAPI + React rewrite is in progress at
[rememberme-product](https://github.com/mlkmas/rememberme-product) and is not yet
stable.

### Roadmap

- Agent layer with tiered autonomy — routine actions execute automatically,
  clinical actions require caregiver confirmation
- Longitudinal participation tracking, so declining speech surfaces as a trend
  rather than an absence
- Multilingual support (the pipeline is language-agnostic; over 60% of people
  living with dementia are in low- and middle-income countries)
- Testing with real caregivers

---

## Built for

[Hack2Heal 2.0 — Global Healthcare Innovation Hackathon](https://hack2heal-2-0.devpost.com/)

## References

- World Health Organization, [Dementia fact sheet](https://www.who.int/news-room/fact-sheets/detail/dementia)
- Livingston G, et al. Dementia prevention, intervention, and care: 2024 report of the *Lancet* standing Commission. *The Lancet* 2024; 404(10452): 572–628.
- Woods B, et al. Reminiscence therapy for dementia. *Cochrane Database of Systematic Reviews* 2018, Issue 3, CD001120.

## Author

Malak Masarwe — [github.com/mlkmas](https://github.com/mlkmas)
