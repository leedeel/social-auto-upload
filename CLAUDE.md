# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`social-auto-upload` (sau) is a one-click multi-platform video / image publishing automation tool. It is mid-refactor: the current mainline is a unified Python CLI (`sau`) plus per-platform agent `skills/`; the Flask Web backend in `sau_backend.py` and the Vue app in `sau_frontend/` are kept only as historical reference and are **not** guaranteed to run against current `uploader/`.

Mainline platforms (CLI + Skills + Web): `douyin`, `kuaishou`, `xiaohongshu`, `bilibili`. Implemented in `uploader/` and exposed via `sau_cli.py`, but **not all of these have a skill yet** — see [Skills](#skills).

Legacy / reference-only (still in `uploader/`, not on the mainline): `tencent_uploader` (视频号), `baijiahao_uploader`, `tk_uploader` (TikTok), `xhs_uploader` (separate legacy path), `youtube_uploader` (CLI only, no skill).

## Repository Layout

```
.
├── sau_cli.py               # Current CLI main entry — defines `sau` subcommands
├── sau_backend.py           # Legacy Flask backend (port 5409) — not the mainline
├── index.html               # Legacy single-file Web frontend (used by sau_backend.py)
├── sau_frontend/            # Legacy Vue + Vite + Element Plus + Pinia frontend (Docker only)
├── sau_backend/             # Historical docs for the Web stack
├── pyproject.toml           # Canonical dep manifest; registers `sau = sau_cli:main`
├── uv.lock                  # Lockfile (uv-managed)
├── Pipfile                  # Legacy pipenv file — not the current install path
├── requirements.txt         # Historical install path — superseded by pyproject.toml
├── Makefile                 # `make setup | run | check | smoke | ...`
├── STARTUP.md               # First-run walkthrough (Web-era)
├── conf.example.py          # Copy to conf.py; runtime config (see Configuration)
├── uploader/
│   ├── douyin_uploader/     # DouYinVideo / DouYinNote / cookie_auth / douyin_setup
│   ├── ks_uploader/         # Kuaishou (KSVideo / KSNote)
│   ├── xiaohongshu_uploader/# XiaoHongShuVideo / XiaoHongShuNote (mainline 小红书)
│   ├── bilibili_uploader/   # runtime.py wraps `biliup` (auto-downloaded on first run)
│   ├── youtube_uploader/    # YouTubeVideo — CLI-only, browser-automation via patchright
│   ├── tencent_uploader/    # 视频号 — legacy
│   ├── xhs_uploader/        # legacy alt path for 小红书
│   ├── baijiahao_uploader/  # reference only
│   ├── tk_uploader/         # TikTok — reference only
│   └── base_video.py        # BaseVideo shared by uploader classes
├── myUtils/                 # Web-era helpers (login.py, auth.py, postVideo.py) — used by sau_backend.py
├── utils/                   # Shared helpers + stealth.min.js (anti-detection injection)
├── skills/                  # Agent skills, one folder per platform (see Skills)
├── docs/                    # install.md, update.md, CLI.md, agent-bootstrap.md, legacy-web.md
├── tests/                   # unittest-based CLI / uploader tests
├── cookiesFile/             # Runtime cookie JSON (gitignored) — `<account_name>.json`
├── videos/                  # Sample / input video files (gitignored)
├── videoFile/               # Web-era upload landing zone (gitignored)
├── db/                      # Web-era SQLite (`database.db`); created by db/createTable.py
├── examples/                # Upstream-direct uploader examples — historical reference only
├── export_douyin_cookie.sh  # Manual cookie export helper for Douyin via VNC
└── start-win.bat            # Windows convenience launcher (Web-era)
```

## Mainline vs. Legacy

This repo has two parallel stacks. **Default to the mainline unless the user explicitly asks for the Web stack.**

| Concern | Mainline (use this) | Legacy Web |
| --- | --- | --- |
| Entry | `sau <platform> <action>` (after `uv pip install -e .`) | `python sau_backend.py` |
| Frontend | CLI only — no UI | `index.html` (local) or `sau_frontend/` (Docker) |
| Browser driver | **patchright** (drop-in Playwright fork, anti-detection) | playwright (Chromium) |
| Install | `uv pip install -e .` + `patchright install chromium` | `pip install -r requirements.txt` + `playwright install chromium` |
| Config | `conf.example.py` → `conf.py` | same file, fewer vars |
| State | `<account_name>.json` cookie per platform under `cookiesFile/` | `user_info` + `file_records` SQLite tables |
| Skills | `skills/<platform>-upload/` for agent use | none |

The Web stack is described in `docs/legacy-web.md`; do not invest in it. The architecture details at the bottom of this file are kept only as a reference for the Web stack.

## Build, Install, Run

### Quick start (mainline)

```bash
uv venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -e .                           # registers `sau` command
PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright" \
  patchright install chromium                 # China-friendly; drop the env var elsewhere
cp conf.example.py conf.py                    # edit BASE_DIR / LOCAL_CHROME_HEADLESS as needed
python db/createTable.py                      # only if you'll touch the Web stack
sau --help                                    # verify install
```

### Make shortcuts (Web-era, but most still useful)

```bash
make help                # list all targets
make setup               # install + config + db (one-shot)
make run                 # python sau_backend.py  (port 5409)
make run-debug           # python cli_main.py — NOTE: this target references a removed file
make check               # python -m py_compile on the Web backend files
make smoke               # curl /login?type=mock against a running backend
make clean-data          # wipe cookiesFile / db / videoFile (interactive)
```

`make run-debug` references `cli_main.py`, which has been removed; running that target will fail. Use `make run` + a separate editor session, or run the CLI mainline directly.

### Tests

```bash
python -m unittest discover -s tests -v
# or a single file:
python -m unittest tests.test_sau_browser_cli -v
```

Tests use `unittest` + `unittest.mock` and do not require a live browser. They live in `tests/` and cover CLI parser contracts, bilibili runtime wiring, douyin declaration fields, and the xiaohongshu uploader.

### Static syntax check (Web-era)

```bash
python -m py_compile sau_backend.py cli_main.py myUtils/login.py myUtils/auth.py myUtils/postVideo.py
```

Zero output = pass. `cli_main.py` doesn't exist anymore, so this command will error — trim it when running.

## CLI (`sau`)

Defined in `sau_cli.py` and registered via `pyproject.toml`'s `[project.scripts]`. Subcommands per platform: `login`, `check`, `upload-video`, `upload-note` (where supported). Common flags:

- `--account <name>` — required; maps to `cookiesFile/<name>.json`
- `--debug`, `--headless` / `--headed` — independent dimensions; default is headless
- `--schedule "YYYY-MM-DD HH:MM"` — auto-switches to scheduled publish; omit for immediate
- `--file`, `--title`, `--desc`, `--tags` (video platforms)
- `--images` (multiple), `--title`, `--note`, `--tags` (image / note platforms)
- `--tid` (Bilibili partition, required), `--thumbnail`, `--thumbnail-landscape`, `--thumbnail-portrait`
- `--product-link`, `--product-title` (Douyin product card)

Examples:

```bash
sau douyin login --account creator
sau douyin upload-video --account creator --file videos/demo.mp4 \
    --title "示例" --desc "示例简介" --tags 运动,训练
sau douyin upload-note --account creator \
    --images videos/1.png videos/2.png --title "图文标题" --note "正文" --tags tag1,tag2

sau bilibili upload-video --account creator --file videos/demo.mp4 \
    --title "示例" --desc "简介" --tid 249 --tags 足球,测试

sau youtube upload-video --account creator --file videos/demo.mp4 \
    --title "示例" --desc "简介" --tags tag1,tag2 \
    --playlist "我的系列" --visibility public
```

Douyin SMS verification during publish: the CLI reads `verify_code.txt` from the project root first, then prompts on a TTY if absent. After success, `verify_code.txt` is deleted.

Bilibili: `biliup` is downloaded on first run and updated on every run; you don't install it manually.

YouTube: blocked in some regions — set `YT_PROXY` in `conf.py` (chromium ignores the system proxy).

## Skills

Per-platform agent skills live in `skills/<platform>-upload/`. Each has `SKILL.md` + `references/{cli-contract,runtime-requirements,troubleshooting}.md` + a `scripts/` folder. Currently shipped:

- `skills/douyin-upload/`
- `skills/kuaishou-upload/`
- `skills/xiaohongshu-upload/`
- `skills/bilibili-upload/`

These skills assume `sau` is already installed and callable. They are NOT a substitute for the CLI — they describe the contract for an agent that shells out to `sau`. The full platform list and CLI contract live in `docs/CLI.md` and `docs/agent-bootstrap.md`.

## Configuration (`conf.py`)

Generated from `conf.example.py`. Vars:

| Var | Purpose |
| --- | --- |
| `BASE_DIR` | Root for relative paths (cookies, videos, db). Defaults to the file's directory. |
| `LOCAL_CHROME_HEADLESS` | `True` for server / CI; `False` to see the QR-scanning browser locally. |
| `LOCAL_CHROME_PATH` | Absolute path to a system Chrome; empty = Playwright/patchright Chromium. |
| `DEBUG_MODE` | Default debug behavior for uploaders. |
| `XHS_SERVER` | `http://127.0.0.1:11901` — used by the legacy 小红书 flow only. Set to `None` if you don't use that path. |
| `YT_PROXY` | e.g. `http://127.0.0.1:7890` — chromium ignores the system proxy, so this is the only way to reach YouTube from blocked regions. |

`sau_cli.py` reads `BASE_DIR` directly; `sau_backend.py` falls back to `Path(__file__).resolve().parent` if `conf.py` is missing, but `myUtils/*` does not — don't skip the `cp conf.example.py conf.py` step.

## Legacy Web Architecture (reference only)

`sau_backend.py` is a single-file Flask app organized into 7 numbered sections:

1. **Config & logging** — loads `conf.py`, wraps myUtils imports in try/except so the server still boots without optional deps.
2. **Static & index** — `/` returns a status string; `/assets/...` serves from local `assets/`.
3. **File management** — `/uploadSave`, `/getFiles`, `/deleteFile`. Videos land in `videoFile/<uuid>_<filename>`; metadata in `file_records`.
4. **Account management** — `/getAccounts`, `/getValidAccounts`, `/updateUserinfo`, `/deleteAccount` (uses `user_info` table). `getValidAccounts` returns DB rows without re-validating cookies; live validation happens at publish time.
5. **SSE login** — `/login?type=<platform>&id=<username>`. Daemon thread + per-request `Queue`; runs an asyncio loop calling the platform's `*_cookie_gen()` from `myUtils.login`. QR codes are base64 PNGs; status is plain text. Termination sentinel tokens: `200`, `500`, `流程结束`, `发生异常`, `错误:`.
6. **Publish** — `/postVideo`. `validate_account_cookie()` launches a headless browser to re-validate each cookie before dispatching to `post_video_<platform>()` in `myUtils.postVideo`. Per-account result — one failure does not block others.
7. **Cookie upload/download** — `/uploadCookie`, `/downloadCookie` (path-traversal guarded).

Flask binds `0.0.0.0:5409`; don't change the port without also updating `index.html` and the Dockerfile.

### Login flow (`myUtils/login.py`)

Each `*_cookie_gen(id, status_queue)` follows the same Playwright pattern: launch chromium with `headless=LOCAL_CHROME_HEADLESS`, call `utils.base_social_media.set_init_script(context)` to inject `utils/stealth.min.js`, navigate to the platform creator page, locate the QR `<img>` via `role/name`, capture it as base64 → SSE, wait up to 200s for `framenavigated`, optionally handle identity verification, save `context.storage_state()` to `cookiesFile/<uuid_v1>.json`, re-run `check_cookie()`, insert a `user_info` row.

`mock` / `test` / `qrcode-test` short-circuit with a static SVG QR — useful for smoke-testing SSE without a real login.

### Publish flow (`myUtils/postVideo.py`)

Each `post_video_<platform>(title, files, tags, account_file, ...)` resolves paths under `cookiesFile/` and `videoFile/`, normalizes tags, optionally generates a next-day schedule, then constructs the platform's `<Platform>Video` class and runs `app.main()` via `asyncio.run`. The Bilibili path additionally calls `bilibili_setup(account_file, handle=True)` first.

### Database (Web-era)

SQLite at `db/database.db`, schema created by `db/createTable.py`:

- `user_info(id, type, filePath, userName, status)` — `type` is the integer 1–5, `filePath` is the cookie JSON filename, `status=1` means the last check passed.
- `file_records(id, filename, filesize, file_path, upload_time)` — `file_path` is the on-disk name in `videoFile/`.

The `type` column is declared `INTEGER` but `sau_backend.py` stores `'5'` (string) for Bilibili — this works only because SQLite is type-flexible; do not rely on it.

### `cli_main.py`

Despite the filename, it is not a CLI. It is a near-verbatim copy of `sau_backend.py` that runs the same Flask app with `debug=True`. **It has been removed from the tree**; references to it in `Makefile`, `STARTUP.md`, and the older `CLAUDE.md` are stale.

## Conventions

- Mainline code lives in `uploader/`, `sau_cli.py`, `utils/`, and `skills/`. `myUtils/` is Web-era.
- `cookiesFile/`, `videos/`, `videoFile/`, and `db/database.db` are runtime artifacts — gitignored.
- A new platform: drop a `uploader/<platform>_uploader/main.py` exposing `<Platform>Video` (and `<Platform>Note` if image upload is needed) with `cookie_auth(...)` and `setup(...)`; wire it into both `sau_cli.py` (CLI dispatch + request dataclass) and `skills/<platform>-upload/` if you want an agent skill.
- Anti-bot: never remove `set_init_script(context)` (or its patchright equivalent) or `utils/stealth.min.js`.
- Per-platform Playwright/patchright launch flags live in each uploader's `setup()`; keep `--lang en-GB` on platforms with locale-sensitive UI.
- Bilibili: do not commit `biliup` binaries; `runtime.py` downloads them.
- When adding a CLI subcommand, also update `docs/CLI.md` and the corresponding `skills/<platform>-upload/references/cli-contract.md`.
- README disclaimer: this project is for personal/learning automation only; respect each platform's ToS.
