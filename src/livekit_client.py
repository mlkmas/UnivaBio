# src/livekit_client.py
import asyncio
import os
import sys
import wave
from datetime import datetime
from pathlib import Path
from livekit import rtc
from dotenv import load_dotenv
import requests
import numpy as np

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical, summarize_transcript_caregiver
from src.schemas import ConversationSegment, ConversationSummary
from src.database import save_conversation, get_settings
from src.patient_assistant import answer_patient_question, detect_emergency

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")


class AudioReceiverAgent:
    """
    Enhanced agent with:
    - Patient identity recognition
    - Assistant mode for answering questions
    - Emergency detection
    """

    def __init__(self):
        self.room = rtc.Room()
        self.audio_stream = None
        self.is_listening = False

        # Audio buffer
        self.audio_buffer = []
        self.is_recording = False
        self.silence_frames = 0
        self.speech_frames = 0

        # Thresholds
        self.SILENCE_THRESHOLD = 50
        self.MIN_SPEECH_FRAMES = 10
        self.ENERGY_THRESHOLD = 300
        self.SAMPLE_RATE = 48000

        # NEW: Track speaker identity
        self.current_speaker = "patient"  # Default to patient
        self.participant_identities = {}  # Map participant.sid -> identity name

        # NEW: Assistant mode
        self.assistant_mode = False
        self.last_emergency_check = datetime.now()

        Path("recordings").mkdir(exist_ok=True)

        print("🎤 AudioReceiverAgent initialized with patient tracking")

    def is_speech(self, audio_frame):
        """Detect speech in audio frame"""
        try:
            if hasattr(audio_frame, 'data'):
                audio_data_bytes = audio_frame.data
            else:
                return False

            audio_data = np.frombuffer(audio_data_bytes, dtype=np.int16)

            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            else:
                rms = 0

            return rms > self.ENERGY_THRESHOLD

        except Exception as e:
            if not hasattr(self, '_error_logged'):
                print(f"⚠️ Error in is_speech: {e}")
                self._error_logged = True
            return False

    def add_frame(self, audio_frame):
        """Add frame and detect conversation boundaries"""
        has_speech = self.is_speech(audio_frame)

        if has_speech:
            self.speech_frames += 1
            self.silence_frames = 0

            if not self.is_recording and self.speech_frames >= self.MIN_SPEECH_FRAMES:
                self.is_recording = True
                speaker_name = self.current_speaker
                print(f"🎙️ Conversation started - Recording ({speaker_name} speaking)...")

            if self.is_recording:
                if hasattr(audio_frame, 'data'):
                    self.audio_buffer.append(audio_frame.data)

        else:
            if self.is_recording:
                self.silence_frames += 1
                if hasattr(audio_frame, 'data'):
                    self.audio_buffer.append(audio_frame.data)

                if self.silence_frames >= self.SILENCE_THRESHOLD:
                    print(f"🛑 Silence detected - Ending conversation")
                    return True

            self.speech_frames = 0

        return False

    async def save_conversation(self):
        """Save, transcribe, and analyze conversation"""
        if not self.audio_buffer or len(self.audio_buffer) < 10:
            print("⚠️ Buffer too short, skipping save")
            self.reset()
            return False

        try:
            # --- FIX: Use local time ---
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            # --- END OF FIX ---

            speaker_label = self.current_speaker
            audio_filename = f"recordings/conversation_{speaker_label}_{timestamp}.wav"

            print(f"💾 Saving conversation from {speaker_label} ({len(self.audio_buffer)} frames)")

            # Save audio
            with wave.open(audio_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(b''.join(self.audio_buffer))

            print(f"✅ Audio saved: {audio_filename}")

            # Transcribe
            print("🤖 Transcribing conversation...")
            transcript = transcribe_audio(audio_filename)

            if not transcript or transcript.startswith("Error"):
                print(f"❌ Transcription failed: {transcript}")
                self.reset()
                return False

            print(f"📝 Transcript: {transcript[:100]}...")

            # Check for emergency if in assistant mode
            settings = get_settings()
            if settings.get('assistant_mode_enabled', False):
                is_emergency, emergency_type = detect_emergency(transcript)
                if is_emergency:
                    print(f"🚨🚨🚨 EMERGENCY DETECTED: {emergency_type} 🚨🚨🚨")

            # Generate summaries
            print("✨ Generating summaries...")
            simple_summary = summarize_transcript_simple(transcript)
            caregiver_summary = summarize_transcript_caregiver(transcript)  # NEW
            clinical_data = summarize_transcript_clinical(transcript)

            if "error" in clinical_data:
                print(f"❌ Summarization failed")
                self.reset()
                return False

            print(f"✅ Summaries generated")
            print(f"   Patient summary: {simple_summary[:50]}...")
            print(f"   Caregiver summary: {caregiver_summary[:50]}...")

            # Save to database
            print("💾 Saving to database...")

            segment = ConversationSegment(
                start_time=current_time,
                end_time=current_time,
                transcript=transcript,
                speaker_identity=speaker_label
            )

            summary = ConversationSummary(
                segment_id=str(segment.id),
                generated_at=current_time, # Use local time
                simple_summary=simple_summary,
                caregiver_summary=caregiver_summary,  # NEW
                **clinical_data
            )

            save_conversation(segment, summary)

            print("🎉 Conversation saved to database!")
            print("=" * 50)

            self.reset()
            return True

        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            import traceback
            traceback.print_exc()
            self.reset()
            return False

    def reset(self):
        """Reset recorder state"""
        self.audio_buffer = []
        self.is_recording = False
        self.silence_frames = 0
        self.speech_frames = 0
        print("🔄 Recorder reset, ready for next conversation")

    async def start(self, identity: str, token: str):
        """Connect to LiveKit room"""
        try:
            print(f"Connecting to {LIVEKIT_URL} as {identity}...")
            await self.room.connect(LIVEKIT_URL, token)
            print(f"✅ Successfully connected to room: {self.room.name}")

            @self.room.on("track_subscribed")
            def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication,
                                    participant: rtc.RemoteParticipant):
                # Track participant identity
                participant_name = participant.identity
                self.participant_identities[participant.sid] = participant_name

                # Determine if this is patient or caregiver
                if "patient" in participant_name.lower():
                    self.current_speaker = "patient"
                elif "caregiver" in participant_name.lower() or "admin" in participant_name.lower():
                    self.current_speaker = "caregiver"
                else:
                    self.current_speaker = participant_name

                print(f"🎵 Track from: {participant_name} (identified as: {self.current_speaker})")

                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    asyncio.ensure_future(self.process_audio_track(track, participant))

            # Check existing participants
            for participant in self.room.remote_participants.values():
                participant_name = participant.identity
                self.participant_identities[participant.sid] = participant_name

                print(f"  - Existing participant: {participant_name}")
                for track_pub in participant.track_publications.values():
                    if track_pub.track and track_pub.kind == rtc.TrackKind.KIND_AUDIO:
                        asyncio.ensure_future(self.process_audio_track(track_pub.track, participant))

        except Exception as e:
            print(f"❌ Error connecting to LiveKit: {e}")
            import traceback
            traceback.print_exc()

    async def process_audio_track(self, track: rtc.Track, participant: rtc.RemoteParticipant):
        """Process incoming audio stream"""
        try:
            participant_name = participant.identity

            # Update current speaker
            if "patient" in participant_name.lower():
                self.current_speaker = "patient"
            elif "caregiver" in participant_name.lower():
                self.current_speaker = "caregiver"
            else:
                self.current_speaker = participant_name

            print(f"📡 Processing audio from: {participant_name} (speaker: {self.current_speaker})")

            audio_stream = rtc.AudioStream(track)
            self.is_listening = True

            frame_count = 0

            async for event in audio_stream:
                frame_count += 1

                if frame_count % 100 == 0:
                    status = "🎙️ RECORDING" if self.is_recording else "👂 Listening"
                    print(
                        f"{status} ({self.current_speaker}) - Frames: {frame_count}, Buffer: {len(self.audio_buffer)}")

                audio_frame = event.frame
                should_save = self.add_frame(audio_frame)

                if should_save:
                    await self.save_conversation()

        except Exception as e:
            print(f"❌ Error processing audio track: {e}")
            import traceback
            traceback.print_exc()

    async def stop(self):
        """Disconnect from room"""
        if self.room.connection_state != rtc.ConnectionState.CONN_DISCONNECTED:
            print("Disconnecting from room...")
            await self.room.disconnect()
            self.is_listening = False
            print("✅ Disconnected")


def get_token(identity: str) -> str:
    """Get access token from token server"""
    try:
        print(f"🎫 Requesting token for: {identity}")
        res = requests.get(f"http://localhost:5000/get_token?identity={identity}", timeout=5)
        res.raise_for_status()
        token_data = res.json()
        print(f"✅ Token received")
        return token_data["token"]
    except requests.RequestException as e:
        print(f"❌ Error getting token: {e}")
        print("=" * 50)
        print("Make sure token server is running:")
        print("  poetry run python src/token_server.py")
        print("=" * 50)
        return None


async def main():
    print("=" * 50)
    print("🎙️ RememberMe LiveKit Agent (Patient Tracking)")
    print("=" * 50)

    token = get_token(identity="rememberme-agent")
    if not token:
        print("❌ Failed to get token")
        return

    agent = AudioReceiverAgent()
    try:
        await agent.start(identity="rememberme-agent", token=token)

        print("\n" + "=" * 50)
        print("✅ Agent running with patient identity tracking")
        print("=" * 50)
        print("\nPatient naming guide:")
        print("  - Name participants 'patient' for patient tracking")
        print("  - Name participants 'caregiver' for caregiver tracking")
        print("\nPress Ctrl+C to stop")
        print("=" * 50 + "\n")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Stopping agent...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.stop()
        print("Agent stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")