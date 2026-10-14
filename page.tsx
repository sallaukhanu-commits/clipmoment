import Link from "next/link";
import { ArrowRight, Captions, Crop, Gauge, Scissors, Sparkles, UploadCloud, Play, FileVideo } from "lucide-react";
import { Logo } from "@/components/Logo";
import { APP_NAME, PLANS, PLATFORMS, SUPABASE_CONFIGURED } from "@/lib/config";
import { DEMO_CLIPS } from "@/lib/demo";
import { DemoBanner } from "@/components/DemoBanner";

const FEATURES = [
  { icon: Sparkles, title: "Moment detection", body: "Finds self-contained moments (insights, stories, debates, advice) instead of cutting at fixed intervals." },
  { icon: Gauge, title: "Estimated engagement score", body: "Each candidate gets a score with a short explanation. It is an estimate of clip quality, not a prediction of views." },
  { icon: Captions, title: "Accurate captions", body: "Word-level timestamps drive animated captions, with speaker labels when diarization is available." },
  { icon: Crop, title: "Vertical reframing", body: "Landscape video is cropped to 9:16. Adjust the crop position per clip." },
  { icon: Scissors, title: "Edit before export", body: "Trim start and end, tweak captions, and pick a caption style with a live preview." },
  { icon: FileVideo, title: "Platform-ready files", body: "Export 1080×1920 MP4 clips suited to Shorts, Reels, and TikTok." },
];

const STEPS = [
  { n: "1", title: "Upload your video", body: "Drop in a podcast, interview, or webinar, or import a supported link." },
  { n: "2", title: "Review ranked moments", body: "The AI transcribes the video and proposes clips, each with a score and reasoning." },
  { n: "3", title: "Edit and export", body: "Adjust timing, captions, and framing, then download your vertical clips." },
];

const FAQ = [
  { q: "Can you guarantee my clips will go viral?", a: "No. Scores are estimates based on the transcript, not forecasts of views or performance." },
  { q: "Which videos can I use?", a: "Files you upload (MP4, MOV, WebM, MKV), or links from providers we can access legitimately. We never bypass logins, DRM, or platform restrictions. If a link can't be imported, upload the file instead." },
  { q: "Do I need the rights to the video?", a: "Yes. Only upload or import content you own or are licensed to repurpose." },
  { q: "Who can see my videos?", a: "Files are stored privately and tied to your account. Row-level security prevents other users from reading them." },
  { q: "Which languages are supported?", a: "That depends on the configured speech-to-text provider." },
];

export default function Home() {
  return (
    <>
      {!SUPABASE_CONFIGURED && <DemoBanner />}
      <header className="sticky top-0 z-20 border-b border-border bg-bg/90 backdrop-blur">
        <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4" aria-label="Main">
          <Logo />
          <div className="hidden items-center gap-6 text-sm text-muted md:flex">
            <a href="#features" className="hover:text-white">Features</a>
            <a href="#how" className="hover:text-white">How it works</a>
            <a href="#pricing" className="hover:text-white">Pricing</a>
            <a href="#faq" className="hover:text-white">FAQ</a>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login" className="rounded-lg px-3 py-1.5 text-sm text-muted hover:text-white">Sign in</Link>
            <Link href="/signup" className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium hover:bg-accent-hover">Get started</Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-16 lg:grid-cols-2 lg:py-24">
          <div>
            <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl">Turn Long Videos Into Their Best Moments</h1>
            <p className="mt-5 max-w-xl text-lg text-muted">
              Upload a podcast, interview, or webinar. {APP_NAME} transcribes it, finds the moments that stand on their own, and
              renders captioned vertical clips you can edit and export.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/signup" className="inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-3 font-medium hover:bg-accent-hover">
                Start Creating Clips <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 font-medium hover:bg-surface2">
                <Play className="h-4 w-4" /> Explore Demo
              </Link>
            </div>
            <p className="mt-4 text-sm text-muted">Default clip length 30–40s, adjustable from 15 to 90s.</p>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-4 shadow-xl" aria-label="Upload interface preview">
            <p className="mb-3 text-xs uppercase tracking-wide text-muted">Interface preview</p>
            <div className="grid place-items-center rounded-xl border border-dashed border-border bg-bg/50 px-6 py-10 text-center">
              <UploadCloud className="h-8 w-8 text-accent" />
              <p className="mt-3 font-medium">Drop a video here</p>
              <p className="text-sm text-muted">MP4, MOV, WebM, MKV</p>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-3">
              {DEMO_CLIPS.map((c) => (
                <div key={c.title} className="rounded-lg border border-border bg-surface2 p-2">
                  <div className="aspect-[9/16] rounded bg-gradient-to-b from-slate-700/60 to-slate-900/80" />
                  <p className="mt-2 line-clamp-2 text-xs font-medium">{c.title}</p>
                  <p className="text-[11px] text-muted">{c.dur} · est. score {c.score}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted">Illustrative example, not real output.</p>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-2xl font-semibold">What it does</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-xl border border-border bg-surface p-5">
                <Icon className="h-5 w-5 text-accent" />
                <h3 className="mt-3 font-medium">{title}</h3>
                <p className="mt-1 text-sm text-muted">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-2xl font-semibold">How it works</h2>
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((s) => (
              <li key={s.n} className="rounded-xl border border-border bg-surface p-5">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-accent-soft font-semibold text-accent">{s.n}</span>
                <h3 className="mt-3 font-medium">{s.title}</h3>
                <p className="mt-1 text-sm text-muted">{s.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-12">
          <h2 className="text-2xl font-semibold">Made for short-form platforms</h2>
          <div className="mt-6 flex flex-wrap gap-3">
            {PLATFORMS.map((p) => (
              <span key={p} className="rounded-full border border-border bg-surface px-4 py-2 text-sm">{p}</span>
            ))}
          </div>
        </section>

        <section id="pricing" className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-2xl font-semibold">Pricing</h2>
          <p className="mt-1 text-sm text-muted">Plans are configurable in <code>src/lib/config.ts</code>. Prices below are placeholders.</p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {PLANS.map((p) => (
              <div key={p.name} className="rounded-xl border border-border bg-surface p-6">
                <h3 className="font-medium">{p.name}</h3>
                <p className="mt-2 text-3xl font-bold">{p.price}</p>
                <p className="text-xs text-muted">{p.note}</p>
                <ul className="mt-4 space-y-2 text-sm text-muted">
                  {p.features.map((f) => <li key={f}>• {f}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-3xl px-4 py-16">
          <h2 className="text-2xl font-semibold">FAQ</h2>
          <div className="mt-6 divide-y divide-border rounded-xl border border-border bg-surface">
            {FAQ.map((f) => (
              <details key={f.q} className="group p-4">
                <summary className="font-medium">{f.q}</summary>
                <p className="mt-2 text-sm text-muted">{f.a}</p>
              </details>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
          <Logo />
          <div className="flex flex-wrap gap-5">
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <Link href="/terms" className="hover:text-white">Terms</Link>
            <a href="mailto:hello@example.com" className="hover:text-white">Contact</a>
            <a href="#features" className="hover:text-white">Product</a>
          </div>
        </div>
      </footer>
    </>
  );
}
