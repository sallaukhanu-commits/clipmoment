"""Provider interfaces so transcription and LLM vendors stay interchangeable."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Word:
    w: str
    start: float
    end: float


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None
    words: list[Word] = field(default_factory=list)


class Transcriber(Protocol):
    def transcribe(self, audio_path: str, offset_sec: float = 0.0) -> list[Segment]: ...


class LLM(Protocol):
    def complete_json(self, system: str, user: str) -> dict: ...


class OpenAITranscriber:
    """OpenAI speech-to-text with word + segment timestamps. Diarization is not provided here."""

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI()

    def transcribe(self, audio_path: str, offset_sec: float = 0.0) -> list[Segment]:
        with open(audio_path, "rb") as f:
            r = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )
        words = [Word(x.word, x.start + offset_sec, x.end + offset_sec) for x in (r.words or [])]
        segs: list[Segment] = []
        for s in r.segments or []:
            s_start, s_end = s.start + offset_sec, s.end + offset_sec
            seg_words = [w for w in words if w.start >= s_start - 0.05 and w.end <= s_end + 0.05]
            segs.append(Segment(s_start, s_end, s.text.strip(), None, seg_words))
        return segs


class AnthropicLLM:
    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = os.environ["LLM_MODEL"]

    def complete_json(self, system: str, user: str) -> dict:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system + "\nRespond with a single valid JSON object and nothing else.",
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        start, end = text.find("{"), text.rfind("}")
        return json.loads(text[start : end + 1])


def get_transcriber() -> Transcriber:
    name = os.getenv("TRANSCRIBER", "openai")
    if name == "openai":
        return OpenAITranscriber()
    raise RuntimeError(f"Unknown TRANSCRIBER '{name}'")


def get_llm() -> LLM:
    name = os.getenv("LLM", "anthropic")
    if name == "anthropic":
        return AnthropicLLM()
    raise RuntimeError(f"Unknown LLM '{name}'")
