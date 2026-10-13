# ClipMoment AI

Turn long podcasts, interviews and webinars into ranked, captioned vertical clips. The product name is configurable via `NEXT_PUBLIC_APP_NAME`.

## What is built

| Area | Status |
|---|---|
| Landing page, pricing (placeholder), FAQ, footer | Done |
| Auth: sign up, sign in, sign out, password recovery (Supabase) | Done |
| Protected dashboard, search/sort, status, failed-job retry, settings | Done |
| Upload with validation, metadata + thumbnail preview, private storage | Done |
| Postgres schema + row-level security + private storage policies | Done |
| Python worker: validate → extract audio → transcribe → analyze → rank → render → verify | Done, tested with FFmpeg |
| Interchangeable transcription / LLM providers (`worker/providers.py`) | OpenAI STT + Anthropic LLM included |
| Demo mode (no Supabase): clearly labeled sample data, uploads disabled | Done |

## Not built yet (be aware)

- **Clip editor and preview page** (trim, caption editing, crop position, style). The DB columns exist (`caption_style`, `crop_x`, start/end); the UI does not.
- **Clip download/export UI.** Rendered MP4s are stored privately under `media/<user_id>/<project_id>/clips/`; signed-URL download buttons still need adding.
- **Speaker diarization and face/active-speaker tracking.** Reframing currently crops around a fixed `crop_x` (default centered).
- **URL import.** Intentionally disabled; the UI tells users to upload a file. Add only via official APIs/authorized mechanisms.
- **Billing / usage limits** (Stripe). Pricing plans are placeholders in `src/lib/config.ts`.
- **Upload byte-progress.** The UI shows an indeterminate "Uploading…" state. For large files use Supabase's resumable (TUS) uploads, which also gives real progress. Check your Supabase plan's max file size.
- **Privacy/Terms pages** are placeholders and need real legal text.
- The spec was truncated after pipeline stage 8, so the **scoring rubric is my default** (`worker/analysis.py`: hook 30%, self-contained 25%, value 25%, completeness 20%). Scores are labeled estimates, never view predictions.

## Setup

### 1. Web app
```bash
npm install
cp .env.example .env.local   # fill in Supabase keys
npm run dev
```
With no Supabase keys the app runs in **demo mode**: sample data only, nothing is uploaded or processed.

### 2. Database
Run `supabase/migrations/001_init.sql` in the Supabase SQL editor (or `supabase db push`). It creates tables, RLS policies, the private `media` bucket and its policies. Enable email auth and set your site URL / redirect URLs (`/auth/callback`) in Supabase Auth settings.

### 3. Worker
Requires `ffmpeg` and `ffprobe` on PATH.
```bash
cd worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # service-role key, OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL
python main.py
pytest -q                    # unit tests for scoring/dedupe
```
The worker polls the `jobs` table. "Generate Clips" in the UI inserts a job (server-side, after verifying ownership under RLS).

## Security notes
- The service-role key is used only in `src/lib/supabase/admin.ts` (server-only) and the worker. Never expose it to the browser.
- API routes verify the session, then check ownership through the user's RLS-scoped client before using elevated access.
- `jobs` and `transcript_segments` are writable only by the service role.

## Verification performed
- `tsc --noEmit` and `next build` pass; pages and API respond correctly in demo mode.
- Worker unit tests pass; FFmpeg render + verify path tested on a synthetic video (1080×1920, correct duration, audio present).
- **Not tested:** live Supabase auth/storage/RLS, and the OpenAI/Anthropic calls (no credentials available here).
