from abc import ABC, abstractmethod
import asyncio
from typing import Any
from faster_whisper import WhisperModel
import structlog
from app.core.exceptions.base import TranscriptionError
from app.core.config.settings import settings

logger = structlog.get_logger(__name__)

class TranscriptionProvider(ABC):
    @abstractmethod
    async def transcribe(self, file_path: str) -> dict[str, Any]:
        pass

class FasterWhisperProvider(TranscriptionProvider):
    _model_instance = None

    def __init__(self, model_size: str | None = None, device: str = "cpu"):
        self.model_size = model_size or settings.WHISPER_MODEL_SIZE
        self.device = device
        self.language = settings.WHISPER_LANGUAGE
        self.initial_prompt = settings.WHISPER_INITIAL_PROMPT

    def _get_model(self) -> WhisperModel:
        if FasterWhisperProvider._model_instance is None:
            try:
                logger.info("Loading faster-whisper model", size=self.model_size, device=self.device)
                FasterWhisperProvider._model_instance = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="int8"
                )
            except Exception as e:
                logger.error("Failed to load faster-whisper model", error=str(e))
                raise TranscriptionError(f"Model initialization failed: {str(e)}")
        return FasterWhisperProvider._model_instance

    async def transcribe(self, file_path: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._transcribe_sync, file_path)

    def _transcribe_sync(self, file_path: str) -> dict[str, Any]:
        try:
            model = self._get_model()
            # Added vad_filter=True to ignore silent/noisy gaps and prevent hallucinations
            # Added temperature=0.0 for deterministic, highly accurate transcription
            segments, info = model.transcribe(
                file_path,
                beam_size=5,
                vad_filter=True,
                temperature=0.0,
                language=self.language,
                initial_prompt=self.initial_prompt,
                condition_on_previous_text=False
            )
            segments_list = []
            full_text = []

            for segment in segments:
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text.append(segment.text.strip())

            raw_text = " ".join(full_text)
            return {
                "raw_text": raw_text,
                "segments": segments_list,
                "duration": info.duration
            }
        except Exception as e:
            logger.error("Transcription operation failed", file_path=file_path, error=str(e))
            raise TranscriptionError(f"Transcription failed: {str(e)}")
