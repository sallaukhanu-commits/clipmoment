-- ClipMoment AI initial schema. Run in the Supabase SQL editor or via `supabase db push`.
create extension if not exists "pgcrypto";

create type project_status as enum ('uploaded','queued','processing','completed','failed');
create type clip_status as enum ('candidate','rendering','completed','failed');
create type job_stage as enum ('validate','extract_audio','transcribe','analyze','candidates','rank','render','verify');
create type job_state as enum ('pending','running','succeeded','failed');

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);

create table projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  source_type text not null check (source_type in ('upload','url')),
  source_url text,
  storage_path text,
  thumbnail_path text,
  duration_sec numeric,
  width int,
  height int,
  file_size_bytes bigint,
  has_audio boolean,
  target_min_sec int not null default 30 check (target_min_sec between 15 and 90),
  target_max_sec int not null default 40 check (target_max_sec between 15 and 90),
  status project_status not null default 'uploaded',
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (target_min_sec <= target_max_sec)
);
create index projects_user_idx on projects(user_id, updated_at desc);

create table transcript_segments (
  id bigserial primary key,
  project_id uuid not null references projects(id) on delete cascade,
  idx int not null,
  start_sec numeric not null,
  end_sec numeric not null,
  speaker text,
  text text not null,
  words jsonb, -- [{w, start, end}]
  unique (project_id, idx)
);

create table clips (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  start_sec numeric not null,
  end_sec numeric not null,
  title text,
  hook text,
  score int check (score between 0 and 100), -- an ESTIMATE, not a prediction of views
  score_breakdown jsonb,
  score_reason text,
  caption_style text not null default 'default',
  crop_x numeric not null default 0.5 check (crop_x between 0 and 1),
  output_path text,
  thumbnail_path text,
  output_duration_sec numeric,
  output_width int,
  output_height int,
  status clip_status not null default 'candidate',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (end_sec > start_sec)
);
create index clips_project_idx on clips(project_id);

create table jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  stage job_stage not null,
  state job_state not null default 'pending',
  attempts int not null default 0,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index jobs_pending_idx on jobs(state, created_at);

-- Row-level security: users only ever see their own rows.
alter table profiles enable row level security;
alter table projects enable row level security;
alter table transcript_segments enable row level security;
alter table clips enable row level security;
alter table jobs enable row level security;

create policy "own profile" on profiles for all using (id = auth.uid()) with check (id = auth.uid());
create policy "own projects" on projects for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own clips" on clips for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "read own jobs" on jobs for select using (user_id = auth.uid());
create policy "own transcript" on transcript_segments for select
  using (exists (select 1 from projects p where p.id = project_id and p.user_id = auth.uid()));
-- Writes to transcript_segments and jobs happen only via the service-role worker (bypasses RLS).

-- Private storage bucket; objects live under <user_id>/...
insert into storage.buckets (id, name, public) values ('media', 'media', false) on conflict do nothing;

create policy "own media read" on storage.objects for select
  using (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "own media insert" on storage.objects for insert
  with check (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "own media delete" on storage.objects for delete
  using (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);

-- Auto-create profile on signup
create function handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into profiles(id, display_name) values (new.id, split_part(new.email, '@', 1));
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users for each row execute function handle_new_user();

create function touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
create trigger projects_touch before update on projects for each row execute function touch_updated_at();
create trigger clips_touch before update on clips for each row execute function touch_updated_at();
create trigger jobs_touch before update on jobs for each row execute function touch_updated_at();
