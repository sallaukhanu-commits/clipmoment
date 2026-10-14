"""FFmpeg / ffprobe helpers. All heavy work streams through ffmpeg; nothing loads whole videos in memory."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from providers import Segment


class MediaError(Exception):
    pass


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise MediaError(f"{cmd[0]} failed: {p.stderr[-800:]}")
    return p.stdout


@dataclass
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    size_bytes: int


def probe(path: str) -> MediaInfo:
    out = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    d = json.loads(out)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), None)
    if v is None:
        raise MediaError("No video stream found")
    num, _, den = (v.get("avg_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    return MediaInfo(
        duration=float(d["format"]["duration"]),
        width=int(v["width"]),
        height=int(v["height"]),
        fps=fps,
        has_audio=any(s.get("codec_type") == "audio" for s in d["streams"]),
        size_bytes=int(d["format"].get("size", os.path.getsize(path))),
    )


def extract_audio_chunks(video: str, workdir: str, chunk_sec: int = 600) -> list[tuple[str, float]]:
    """Mono 16 kHz MP3 chunks (small enough for provider upload limits). Returns (path, offset_sec)."""
    pattern = str(Path(workdir) / "audio_%04d.mp3")
    _run([
        "ffmpeg", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
        "-f", "segment", "-segment_time", str(chunk_sec), "-reset_timestamps", "1", pattern,
    ])
    files = sorted(Path(workdir).glob("audio_*.mp3"))
    if not files:
        raise MediaError("Audio extraction produced no files")
    return [(str(f), i * chunk_sec) for i, f in enumerate(files)]


def _ass_time(t: float) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(segments: list[Segment], clip_start: float, clip_end: float, out: str, words_per_line: int = 4) -> bool:
    """Write an ASS subtitle file from word timestamps. Returns False if no words fall in range."""
    words = [w for s in segments for w in s.words if w.start >= clip_start - 0.05 and w.end <= clip_end + 0.05]
    if not words:
        return False
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BorderStyle,Outline,Shadow,Alignment,MarginV",
        "Style: Default,Arial,72,&H00FFFFFF,&H00000000,1,5,0,2,260", "",
        "[Events]", "Format: Layer,Start,End,Style,Text",
    ]
    for i in range(0, len(words), words_per_line):
        grp = words[i : i + words_per_line]
        text = " ".join(w.w.strip() for w in grp).upper()
        lines.append(f"Dialogue: 0,{_ass_time(grp[0].start - clip_start)},{_ass_time(grp[-1].end - clip_start)},Default,{text}")
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    return True


def render_clip(video: str, out: str, start: float, end: float, crop_x: float, ass: str | None, info: MediaInfo) -> None:
    """Cut, crop to 9:16 around crop_x (0..1), scale to 1080x1920, burn captions."""
    crop_w = min(info.width, int(info.height * 9 / 16))
    crop_w -= crop_w % 2
    x = int((info.width - crop_w) * min(max(crop_x, 0), 1))
    vf = f"crop={crop_w}:{info.height}:{x}:0,scale=1080:1920:flags=lanczos"
    if ass:
        vf += f",subtitles='{ass.replace(chr(92), '/').replace(':', chr(92) + ':')}'"
    _run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", video,
        "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out,
    ])


def thumbnail(video: str, out: str, at: float) -> None:
    _run(["ffmpeg", "-y", "-ss", f"{at:.3f}", "-i", video, "-frames:v", "1", "-vf", "scale=480:-2", out])


def verify_clip(path: str, expected_sec: float, expect_audio: bool, tol: float = 1.5) -> MediaInfo:
    """Raises MediaError unless the file exists, is readable, and matches expectations."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        raise MediaError("Output file missing or empty")
    info = probe(path)
    if (info.width, info.height) != (1080, 1920):
        raise MediaError(f"Unexpected dimensions {info.width}x{info.height}")
    if abs(info.duration - expected_sec) > tol:
        raise MediaError(f"Duration {info.duration:.1f}s differs from expected {expected_sec:.1f}s")
    if expect_audio and not info.has_audio:
        raise MediaError("Expected audio track is missing")
    return info
