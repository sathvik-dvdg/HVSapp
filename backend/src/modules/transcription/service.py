# app/services/asr_service.py
import asyncio
import logging
from typing import AsyncGenerator
from contextlib import contextmanager

from fastapi import WebSocket
from google.cloud import speech
from google.api_core.exceptions import DeadlineExceeded, Cancelled

# Import project components
from src.modules.transcription.schemas import SessionState
from src.websocket.connection_manager import manager
from src.db.session import SessionLocal 
from src.modules.patients.note_models import ClinicalNote, NoteType

# --- ASR Configuration ---
ASR_RATE_HZ = 16000
ASR_LANGUAGE_CODE = "en-US"

log = logging.getLogger(__name__)

@contextmanager
def get_db_session():
    """Context manager for safe DB operations in async threads."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_asr_config() -> speech.RecognitionConfig:
    return speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=ASR_RATE_HZ,
        language_code=ASR_LANGUAGE_CODE,
        enable_automatic_punctuation=True,
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=1,
            max_speaker_count=2,
        ),
        model="medical_dictation",
        use_enhanced=True
    )

async def audio_stream_generator(state: SessionState) -> AsyncGenerator[speech.StreamingRecognizeRequest, None]:
    log.info(f"[{state.id}] Starting audio stream generator...")
    yield speech.StreamingRecognizeRequest(streaming_config=speech.StreamingRecognitionConfig(
        config=get_asr_config(),
        interim_results=True,
        single_utterance=False
    ))

    while state.is_active:
        try:
            chunk = await asyncio.wait_for(state.audio_queue.get(), timeout=5.0) 
            if chunk is None:
                log.info(f"[{state.id}] Received 'None' signal, ending audio stream generator.")
                break 
            yield speech.StreamingRecognizeRequest(audio_content=chunk)
        except asyncio.TimeoutError:
            if not state.is_active:
                log.warning(f"[{state.id}] State inactive during queue timeout, stopping generator.")
                break
            continue
        except Exception as e:
            log.error(f"[{state.id}] Audio generator error: {e}", exc_info=True)
            break
            
    log.info(f"[{state.id}] Audio stream generator finished.")

async def process_dictation_and_save_note(websocket: WebSocket, state: SessionState):
    try:
        client = speech.SpeechAsyncClient()
        log.info(f"[{state.id}] Google Speech Client initialized for dictation.")

        requests = audio_stream_generator(state)
        responses: AsyncGenerator[speech.StreamingRecognizeResponse, None] = await client.streaming_recognize(
            requests=requests,
            timeout=300
        )

        async for response in responses:
            if not state.is_active or state.id not in manager.active_connections:
                log.warning(f"[{state.id}] WebSocket closed during ASR, stopping processing.")
                break

            if not response.results: continue
            result = response.results[0]
            if not result.alternatives: continue

            transcript_fragment = result.alternatives[0].transcript
            is_final = result.is_final

            await manager.send_json(state.id, {
                "type": "transcript_update",
                "text": transcript_fragment,
                "is_final": is_final,
            })
            
            if is_final:
                state.final_transcript += transcript_fragment.strip() + " "

        log.info(f"[{state.id}] ASR stream processing finished. Final transcript length: {len(state.final_transcript)}")

        # Save Final Note to Database safely using context manager
        if state.final_transcript and state.encounter_id and state.author_id and state.note_type:
            log.info(f"[{state.id}] Attempting to save final note to database...")
            
            def _save_note_sync(encounter_id, transcript, author_id, note_type):
                with get_db_session() as db:
                    note = ClinicalNote(
                        encounter_id=encounter_id,
                        content=transcript,
                        author_id=author_id,
                        note_type=note_type
                    )
                    db.add(note)
            
            await asyncio.to_thread(_save_note_sync, state.encounter_id, state.final_transcript, state.author_id, state.note_type)

    except DeadlineExceeded:
        log.warning(f"[{state.id}] ASR stream timeout (e.g., 5 mins of silence).")
        await manager.send_json(state.id, {"status": "timeout", "message": "ASR stream timed out."})
    except Cancelled:
        log.info(f"[{state.id}] ASR stream cancelled (expected on disconnect/end).")
    except Exception as e:
        log.error(f"[{state.id}] CRITICAL ASR Service Error: {e}", exc_info=True)
        await manager.send_json(state.id, {"status": "asr_error", "message": f"ASR processing failed: {type(e).__name__}"})
    finally:
        state.is_active = False
        log.info(f"[{state.id}] process_dictation_and_save_note finished.")
