# kyletechcorner Portfolio — project context for Claude Code

Public showcase site ("Kyle's Tech Corner") presenting the homelab projects. Plain static HTML/CSS, hosted on GitHub (pushes to `main` deploy the live site). This is the **outward-facing layer** — when a project ships or changes materially, update its page here.

## Quick facts — don't re-ask Kyle for these

- **Live site:** https://kyletechcorner.com  (homelab page: https://kyletechcorner.com/homelab.html)
- **Local repo:** `~/Projects/kyletechcorner`  ·  **GitHub remote:** `GrayWolf8856/kyletechcorner-preview` (private). Pushing `main` updates the live GitHub-hosted site.
- **Obsidian vault (source of truth):** `~/Documents/Obsidian Vault` — portfolio note at `Web/kyletechcorner Portfolio.md`; homelab project detail at `Infrastructure/Homelab Automation/Homelab Automation.md`.
- **Homelab scripts** live at `~/.homelab` (weather alerts, Telnyx SMS, Pushover, healthchecks heartbeat, balance monitor). SMS cost of record: `$0.0085`/segment (`config.json` → `sms_cost_per_segment`); 10DLC setup was ~$15–20 one-time.
- **Git identity:** GrayWolf8856. Push HTTPS auth uses `kyleecosper@gmail.com` via the macOS keychain — `gh` is NOT installed, so authenticate with plain `git` (keychain) rather than `gh`.
- **Auth safety:** never ask Kyle to paste a GitHub token into a command, and never put one on a command line (it leaks into shell history/logs). The keychain already holds working push credentials.
- **The live site is canonical.** On 2026-07-15 a stale *flat*-layout snapshot in this local clone diverged from the live *folder-based* layout (`projects/`, `projects/plant-hub/`, `fishtank/`). Always base changes on `origin/main`, not on old local pages.

## Structure (live / folder-based)

`index.html` landing · `about.html` · `homelab.html` · `projects/index.html` (project index) · `projects/plant-hub/` · `fishtank/index.html` · `notifications.html` (SMS Terms) · `privacy.html` · `style.css` + `images/` + `files/`.

## Run
Static — open `index.html`, or serve the folder with any static server (`python3 -m http.server`).

## Working agreements (Kyle + Claude)

**Keep Obsidian in sync.** Update `~/Documents/Obsidian Vault/Web/kyletechcorner Portfolio.md` when pages are added/changed, and reflect status in the relevant project note.

**Version control.** After a meaningful change: `git add -A && git commit -m "..." && git push`. No secrets in the repo (`secrets.env` stays git-ignored).
