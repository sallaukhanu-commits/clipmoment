"""Moment detection, scoring and de-duplication.

NOTE: the original spec's scoring section was cut off, so this rubric is a documented default.
Scores are ESTIMATES of clip quality based on transcript content, not predictions of views.
"""
from __future__ import annotations

from dataclasses import dataclass

from providers import LLM, Segment

RUBRIC = {  # weights sum to 1.0
    "hook": 0.30,          # does the first sentence grab attention?
    "self_contained": 0.25,  # makes sense without the rest of the episode
    "value": 0.25,         # insight, advice, story, humor, or emotion
    "completeness": 0.20,  # starts/ends on complete thoughts, no awkward cut
}

SYSTEM = """You select short-form clips from a podcast/video transcript.
Find self-contained moments: strong openings, surprising insights, practical advice, debates,
emotional moments, concise stories, funny moments, useful explanations.
Rules:
- Each clip must start and end on complete sentences, using the provided segment index boundaries.
- Duration must be within the requested range.
- Avoid near-duplicate topics. Prefer variety.
- Do not invent content; only reference what is in the transcript.
Return JSON: {"candidates":[{"start_idx":int,"end_idx":int,"title":str,"hook":str,
"scores":{"hook":0-100,"self_contained":0-100,"value":0-100,"completeness":0-100},"reason":str}]}"""


@dataclass
class Candidate:
    start: float
    end: float
    title: str
    hook: str
    score: int
    breakdown: dict
    reason: str


def _format_transcript(segs: list[Segment]) -> str:
    return "\n".join(f"[{i}] ({s.start:.1f}-{s.end:.1f}) {s.text}" for i, s in enumerate(segs))


def weighted_score(scores: dict) -> int:
    total = sum(RUBRIC[k] * max(0, min(100, float(scores.get(k, 0)))) for k in RUBRIC)
    return round(total)


def overlap_ratio(a: Candidate, b: Candidate) -> float:
    inter = max(0.0, min(a.end, b.end) - max(a.start, b.start))
    return inter / max(1e-6, min(a.end - a.start, b.end - b.start))


def dedupe(cands: list[Candidate], max_overlap: float = 0.3) -> list[Candidate]:
    kept: list[Candidate] = []
    for c in sorted(cands, key=lambda x: -x.score):
        if all(overlap_ratio(c, k) <= max_overlap for k in kept):
            kept.append(c)
    return kept


def _windows(segs: list[Segment], window_sec: float = 1500, overlap_sec: float = 120) -> list[tuple[int, int]]:
    """Split very long transcripts into overlapping index windows so prompts stay manageable."""
    if not segs:
        return []
    out, i = [], 0
    while i < len(segs):
        j = i
        while j < len(segs) and segs[j].end - segs[i].start < window_sec:
            j += 1
        out.append((i, max(j, i + 1)))
        if j >= len(segs):
            break
        k = j
        while k > i and segs[j - 1].end - segs[k - 1].start < overlap_sec:
            k -= 1
        i = max(k - 1, i + 1)
    return out


def find_candidates(llm: LLM, segs: list[Segment], min_sec: int, max_sec: int, max_per_window: int = 8) -> list[Candidate]:
    results: list[Candidate] = []
    for lo, hi in _windows(segs):
        window = segs[lo:hi]
        user = (
            f"Target clip duration: {min_sec}-{max_sec} seconds. Return up to {max_per_window} candidates.\n"
            f"Transcript (indices are global):\n"
            + "\n".join(f"[{lo + i}] ({s.start:.1f}-{s.end:.1f}) {s.text}" for i, s in enumerate(window))
        )
        data = llm.complete_json(SYSTEM, user)
        for c in data.get("candidates", []):
            try:
                a, b = int(c["start_idx"]), int(c["end_idx"])
                if not (0 <= a <= b < len(segs)):
                    continue
                start, end = segs[a].start, segs[b].end
                dur = end - start
                if dur < min_sec - 3 or dur > max_sec + 3:  # small tolerance for sentence boundaries
                    continue
                scores = c.get("scores", {})
                results.append(Candidate(start, end, str(c.get("title", ""))[:120], str(c.get("hook", ""))[:240],
                                         weighted_score(scores), {k: scores.get(k) for k in RUBRIC}, str(c.get("reason", ""))[:400]))
            except (KeyError, ValueError, TypeError):
                continue
    return dedupe(results)
