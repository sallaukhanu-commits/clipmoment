"""Thin Supabase data layer for the worker (uses the service-role key; bypasses RLS)."""
from __future__ import annotations

import os
from typing import Any

from supabase import Client, create_client

_client: Client | None = None
BUCKET = os.getenv("STORAGE_BUCKET", "media")


def sb() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    return _client


def claim_job() -> dict[str, Any] | None:
    """Claim the oldest pending job. Optimistic update guards against double-claiming."""
    res = sb().table("jobs").select("*").eq("state", "pending").order("created_at").limit(1).execute()
    if not res.data:
        return None
    job = res.data[0]
    upd = (
        sb().table("jobs").update({"state": "running", "attempts": job["attempts"] + 1})
        .eq("id", job["id"]).eq("state", "pending").execute()
    )
    return job if upd.data else None


def set_job(job_id: str, state: str, error: str | None = None) -> None:
    sb().table("jobs").update({"state": state, "error": error}).eq("id", job_id).execute()


def set_project(project_id: str, **fields: Any) -> None:
    sb().table("projects").update(fields).eq("id", project_id).execute()


def get_project(project_id: str) -> dict[str, Any]:
    return sb().table("projects").select("*").eq("id", project_id).single().execute().data


def download(path: str, dest: str) -> None:
    data = sb().storage.from_(BUCKET).download(path)
    with open(dest, "wb") as f:
        f.write(data)


def upload(path: str, local: str, content_type: str) -> None:
    with open(local, "rb") as f:
        sb().storage.from_(BUCKET).upload(path, f, {"content-type": content_type, "upsert": "true"})
