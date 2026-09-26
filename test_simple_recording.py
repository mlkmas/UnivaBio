# test_simple_recording.py
"""
Simple test to record audio, transcribe, and save to database
WITHOUT using LiveKit - to test the pipeline
"""
from src.audio_recorder import AudioRecorder
from src.transcriber import transcribe_audio
from src.summarizer import summarize_transcript_simple, summarize_transcript_clinical, summarize_transcript_caregiver
from src.schemas import ConversationSegment, ConversationSummary
from src.database import save_conversation
from datetime import datetime
import os

print("=" * 70)
print("🧪 SIMPLE RECORDING TEST (No LiveKit)")
print("=" * 70)
print()
print("This test will:")
print("1. Record 10 seconds of audio from your microphone")
print("2. Transcribe it")
print("3. Generate summaries")
print("4. Save to database")
print("5. Check if it appears in dashboard")
print()
print("=" * 70)

input("Press Enter when ready to start 10-second recording...")

try:
    # Step 1: Record audio
    print("\n🎤 Recording for 10 seconds...")
    print("SPEAK NOW! Say something like:")
    print("  'Hello, today is a nice day. I spoke with my daughter Sarah.'")
    print()

    recorder = AudioRecorder()
    output_file = "test_recording.wav"
    recorder.record(duration_seconds=10, output_file=output_file)
    recorder.cleanup()

    print("✅ Recording complete!")

    # Step 2: Transcribe
    print("\n🤖 Transcribing...")
    transcript = transcribe_audio(output_file)

    if not transcript or transcript.startswith("Error"):
        print(f"❌ Transcription failed: {transcript}")
        exit(1)

    print(f"✅ Transcript: {transcript}")

    # Step 3: Generate summaries
    print("\n✨ Generating summaries...")

    simple_summary = summarize_transcript_simple(transcript)
    print(f"✅ Patient summary: {simple_summary[:100]}...")

    caregiver_summary = summarize_transcript_caregiver(transcript)
    print(f"✅ Caregiver summary: {caregiver_summary[:100]}...")

    clinical_data = summarize_transcript_clinical(transcript)

    if "error" in clinical_data:
        print(f"❌ Clinical summary failed")
        exit(1)

    print(f"✅ Clinical data: {clinical_data.get('patient_mood', 'N/A')}")

    # Step 4: Save to database
    print("\n💾 Saving to database...")

    start_time = datetime.now()
    end_time = datetime.now()

    segment = ConversationSegment(
        start_time=start_time,
        end_time=end_time,
        transcript=transcript,
        speaker_identity="test_user"
    )

    summary = ConversationSummary(
        segment_id=str(segment.id),
        simple_summary=simple_summary,
        caregiver_summary=caregiver_summary,
        **clinical_data
    )

    save_conversation(segment, summary)

    print("✅ Saved to database!")

    # Step 5: Verify it's there
    print("\n🔍 Verifying in database...")

    from src.database import get_all_conversations

    conversations = get_all_conversations()

    # Find our conversation (should be most recent)
    found = False
    for conv in conversations[:5]:  # Check last 5
        if conv.get('simple_summary') == simple_summary:
            found = True
            print("✅ Found in database!")
            print(f"   Generated at: {conv.get('generated_at')}")
            print(f"   Participant: {conv.get('participant')}")
            break

    if not found:
        print("❌ NOT FOUND in database!")
        print("   Database may not be saving correctly")

    # Clean up
    try:
        os.remove(output_file)
    except:
        pass

    print("\n" + "=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)
    print()

    if found:
        print("✅ SUCCESS! The pipeline works!")
        print()
        print("Next steps:")
        print("1. Go to Caregiver Dashboard")
        print("2. Look for your test conversation")
        print("3. If it's there, the problem is ONLY with LiveKit connection")
        print("4. Fix LiveKit credentials and recording will work")
    else:
        print("❌ PIPELINE HAS ISSUES")
        print()
        print("The problem is NOT just LiveKit.")
        print("Check:")
        print("1. MongoDB connection")
        print("2. Database saving function")
        print("3. OpenAI API key")

    print()
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()