"""Staged processing pipeline. A stage only advances after the previous one succeeded;
a clip is marked completed only after its output file is verified."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import db
from analysis import find_candidates
from media import MediaError, build_ass, extract_audio_chunks, probe, render_clip, thumbnail, verify_clip
from providers import Segment, Word, get_llm, get_transcriber

log = logging.getLogger("pipeline")
MAX_CLIPS_TO_RENDER = 10


def _stage(job_id: str, stage: str) -> None:
    db.sb().table("jobs").update({"stage": stage}).eq("id", job_id).execute()
    log.info("stage=%s job=%s", stage, job_id)


def run_job(job: dict) -> None:
    project_id, user_id, job_id = job["project_id"], job["user_id"], job["id"]
    max_dur_min = float(__import__("os").getenv("MAX_DURATION_MIN", "180"))
    try:
        db.set_project(project_id, status="processing", error_message=None)
        project = db.get_project(project_id)
        if not project.get("storage_path"):
            raise MediaError("Project has no uploaded source file")

        with tempfile.TemporaryDirectory(prefix="clipmoment_") as tmp:
            src = str(Path(tmp) / "source")
            db.download(project["storage_path"], src)

            # 1. validate
            _stage(job_id, "validate")
            info = probe(src)
            if info.duration > max_dur_min * 60:
                raise MediaError(f"Video is longer than the {max_dur_min:.0f}-minute limit")
            if not info.has_audio:
                raise MediaError("Video has no audio track; transcription is not possible")
            thumb = str(Path(tmp) / "thumb.jpg")
            thumbnail(src, thumb, min(info.duration / 4, 30))
            thumb_path = f"{user_id}/{project_id}/thumb.jpg"
            db.upload(thumb_path, thumb, "image/jpeg")
            db.set_project(project_id, duration_sec=info.duration, width=info.width, height=info.height,
                           file_size_bytes=info.size_bytes, has_audio=True, thumbnail_path=thumb_path)

            # 2. extract audio
            _stage(job_id, "extract_audio")
            chunks = extract_audio_chunks(src, tmp)

            # 3. transcribe
            _stage(job_id, "transcribe")
            transcriber = get_transcriber()
            segments: list[Segment] = []
            for path, offset in chunks:
                segments.extend(transcriber.transcribe(path, offset))
            if not segments:
                raise MediaError("Transcription returned no speech")
            segments.sort(key=lambda s: s.start)
            db.sb().table("transcript_segments").delete().eq("project_id", project_id).execute()
            rows = [{
                "project_id": project_id, "idx": i, "start_sec": s.start, "end_sec": s.end,
                "speaker": s.speaker, "text": s.text,
                "words": [{"w": w.w, "start": w.start, "end": w.end} for w in s.words],
            } for i, s in enumerate(segments)]
            for i in range(0, len(rows), 500):
                db.sb().table("transcript_segments").insert(rows[i : i + 500]).execute()

            # 4-6. analyze, candidates, rank
            _stage(job_id, "analyze")
            cands = find_candidates(get_llm(), segments, project["target_min_sec"], project["target_max_sec"])
            _stage(job_id, "rank")
            cands = cands[:MAX_CLIPS_TO_RENDER]
            if not cands:
                raise MediaError("No suitable clip moments were found in this video")
            db.sb().table("clips").delete().eq("project_id", project_id).execute()
            inserted = db.sb().table("clips").insert([{
                "project_id": project_id, "user_id": user_id, "start_sec": c.start, "end_sec": c.end,
                "title": c.title, "hook": c.hook, "score": c.score, "score_breakdown": c.breakdown,
                "score_reason": c.reason, "status": "rendering",
            } for c in cands]).execute().data

            # 7-8. render + verify
            _stage(job_id, "render")
            ok = 0
            for clip in inserted:
                try:
                    out = str(Path(tmp) / f"{clip['id']}.mp4")
                    ass_file = str(Path(tmp) / f"{clip['id']}.ass")
                    has_caps = build_ass(segments, clip["start_sec"], clip["end_sec"], ass_file)
                    render_clip(src, out, clip["start_sec"], clip["end_sec"], clip["crop_x"], ass_file if has_caps else None, info)
                    _stage(job_id, "verify")
                    expected = clip["end_sec"] - clip["start_sec"]
                    out_info = verify_clip(out, expected, expect_audio=True)
                    cthumb = str(Path(tmp) / f"{clip['id']}.jpg")
                    thumbnail(out, cthumb, min(1.0, out_info.duration / 2))
                    out_path = f"{user_id}/{project_id}/clips/{clip['id']}.mp4"
                    db.upload(out_path, out, "video/mp4")
                    db.upload(out_path.replace(".mp4", ".jpg"), cthumb, "image/jpeg")
                    db.sb().table("clips").update({
                        "status": "completed", "output_path": out_path, "thumbnail_path": out_path.replace(".mp4", ".jpg"),
                        "output_duration_sec": out_info.duration, "output_width": out_info.width, "output_height": out_info.height,
                    }).eq("id", clip["id"]).execute()
                    ok += 1
                except Exception as e:  # one bad clip must not sink the others
                    log.exception("clip %s failed", clip["id"])
                    db.sb().table("clips").update({"status": "failed"}).eq("id", clip["id"]).execute()
            if ok == 0:
                raise MediaError("All clips failed to render or verify")

        db.set_project(project_id, status="completed")
        db.set_job(job_id, "succeeded")
    except Exception as e:
        log.exception("job %s failed", job_id)
        msg = str(e)[:500]
        db.set_project(project_id, status="failed", error_message=msg)
        db.set_job(job_id, "failed", msg)
