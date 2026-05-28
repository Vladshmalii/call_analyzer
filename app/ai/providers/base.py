from abc import ABC, abstractmethod
from typing import Any

class AIProvider(ABC):
    @abstractmethod
    async def analyze_transcript(self, transcript_text: str) -> dict[str, Any]:
        pass
