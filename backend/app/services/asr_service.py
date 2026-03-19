# app/services/asr_service.py
import asyncio
import logging
from typing import AsyncGenerator

from fastapi import WebSocket
from google.cloud import speech
from google.api_core.exceptions import DeadlineExceeded, Cancelled

# Import project components
from app.schemas.session import SessionState
from app.utils.connection_manager import manager # WebSocket manager
from app.db.session import SessionLocal # Import SessionLocal to create a DB session
from app.services import note_service # Import the note service
from app.models.note import NoteType # Import the enum

# --- ASR Configuration ---
# Must match the audio format sent from the frontend app
ASR_RATE_HZ = 16000
ASR_LANGUAGE_CODE = "en-US"

log = logging.getLogger(__name__)

def get_asr_config() -> speech.RecognitionConfig:
    """Returns the Google Speech RecognitionConfig object."""
    return speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=ASR_RATE_HZ,
        language_code=ASR_LANGUAGE_CODE,
        enable_automatic_punctuation=True,
        # Diarization can distinguish speakers (e.g., doctor vs. nurse)
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=1,
            max_speaker_count=2,
        ),
        # Use an enhanced model optimized for medical dictation
        model="medical_dictation",
        use_enhanced=True
    )

async def audio_stream_generator(state: SessionState) -> AsyncGenerator[speech.StreamingRecognizeRequest, None]:
    """
    Generator that yields audio chunks from the session's queue to the Google API.
    This runs concurrently with the WebSocket receive loop.
    """
    log.info(f"[{state.id}] Starting audio stream generator...")
    
    # 1. Yield the ASR Configuration Request FIRST
    yield speech.StreamingRecognizeRequest(streaming_config=speech.StreamingRecognitionConfig(
        config=get_asr_config(),
        interim_results=True, # Critical for real-time updates
        single_utterance=False
    ))

    # 2. Continuously yield audio chunks from the queue
    while state.is_active:
        try:
            # Wait for a chunk from the queue
            chunk = await asyncio.wait_for(state.audio_queue.get(), timeout=5.0) 
            
            if chunk is None:
                log.info(f"[{state.id}] Received 'None' signal, ending audio stream generator.")
                break # Exit the generator if the session is finished
            
            yield speech.StreamingRecognizeRequest(audio_content=chunk)
        
        except asyncio.TimeoutError:
            # If queue is empty for 5s, check if state is still active
            if not state.is_active:
                log.warning(f"[{state.id}] State inactive during queue timeout, stopping generator.")
                break
            continue # Otherwise, just keep waiting
        except Exception as e:
            log.error(f"[{state.id}] Audio generator error: {e}", exc_info=True)
            break
            
    log.info(f"[{state.id}] Audio stream generator finished.")


async def process_dictation_and_save_note(websocket: WebSocket, state: SessionState):
    """
    Handles the entire ASR streaming task:
    1. Calls Google ASR API with the audio stream generator.
    2. Sends live transcript feedback to the client via WebSocket.
    3. Accumulates the final transcript.
    4. Saves the final transcript to the database as a ClinicalNote.
    """
    db: Session | None = None # Initialize db session variable for cleanup
    try:
        # Initialize Google Speech Client (authenticates via env variable)
        client = speech.SpeechAsyncClient()
        log.info(f"[{state.id}] Google Speech Client initialized for dictation.")

        requests = audio_stream_generator(state)
        log.info(f"[{state.id}] Audio stream generator created.")

        # Start streaming recognition API call
        responses: AsyncGenerator[speech.StreamingRecognizeResponse, None] = await client.streaming_recognize(
            requests=requests,
            timeout=300 # 5-minute inactivity timeout
        )
        log.info(f"[{state.id}] Google streaming_recognize called, awaiting responses...")

        # Process responses asynchronously as they come in
        async for response in responses:
            if not state.is_active or state.id not in manager.active_connections:
                log.warning(f"[{state.id}] WebSocket closed during ASR, stopping processing.")
                break # Stop processing if client disconnected

            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue

            transcript_fragment = result.alternatives[0].transcript
            is_final = result.is_final

            # 1. Send live transcript update back to the app
            await manager.send_json(state.id, {
                "type": "transcript_update",
                "text": transcript_fragment,
                "is_final": is_final,
            })
            
            # 2. Accumulate the final transcript string
            if is_final:
                state.final_transcript += transcript_fragment.strip() + " "
                log.debug(f"[{state.id}] Appended final segment. Total length: {len(state.final_transcript)}")

        # --- ASR Stream Finished ---
        log.info(f"[{state.id}] ASR stream processing finished. Final transcript length: {len(state.final_transcript)}")

        # 3. Save Final Note to Database
        if state.final_transcript and state.encounter_id and state.author_id and state.note_type:
            log.info(f"[{state.id}] Attempting to save final note to database...")
            
            # Create a NEW database session for this async task
            db = SessionLocal()
            
            # Run the synchronous DB operation in a separate thread pool
            saved_note = await asyncio.to_thread(
                note_service.create_note,
                db=db,

    except DeadlineExceeded:
        log.warning(f"[{state.id}] ASR stream timeout (e.g., 5 mins of silence).")
        await manager.send_json(state.id, {"status": "timeout", "message": "ASR stream timed out."})
    except Cancelled:
        log.info(f"[{state.id}] ASR stream cancelled (expected on disconnect/end).")
    except Exception as e:
        log.error(f"[{state.id}] CRITICAL ASR Service Error: {e}", exc_info=True)
        await manager.send_json(state.id, {"status": "asr_error", "message": f"ASR processing failed: {type(e).__name__}"})
    finally:
        state.is_active = False # Ensure generator stops
        if db: # Close the specific DB session we opened for this task
            db.close()
            log.debug(f"[{state.id}] DB session for note saving closed.")
        log.info(f"[{state.id}] process_dictation_and_save_note finished.")