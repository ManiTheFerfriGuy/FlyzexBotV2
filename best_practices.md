# 📘 Project Best Practices

## 1. Project Purpose
FlyzexBot is an asynchronous Telegram bot with a glassmorphism UI and a companion FastAPI web app. It manages a guild onboarding process (applications, approvals/denials), admin management, XP leaderboards, and cups (competitions). Data is encrypted at rest and optionally exported to an SQLite backup. The project is primarily Persian-first with English support, and emphasizes safe rendering of user-generated content and robust async I/O.

## 2. Project Structure
- Root
  - `bot.py`: Application entrypoint for the Telegram bot (python-telegram-bot v20 async). Builds handlers, configures analytics, storage, rate limits, and registers command handlers.
  - `requirements.txt`: Python dependencies.
  - `README.md`: Setup and run instructions (FA).
  - `data/`: Encrypted storage and SQLite backup output (ignored by VCS, .gitkeep present).
  - `config/`
    - `settings.example.yaml`: Example configuration (copy to `settings.yaml`).
  - `cachetools/`: Local package stub; tests ensure expected behavior for LRUCache.pop semantics.
  - `tests/`: Pytest test suite targeting handlers, storage, escaping, and cache tools.
  - `webapp/` (FastAPI-based admin panel)
    - `server.py`: ASGI app exposing read/write endpoints for admins, XP, cups, and insights.
    - `index.html`: Static glass UI.
    - `static/`: `app.js`, `glass_panel.css` for client logic and styling.
- Package `flyzexbot/`
  - `config.py`: Settings loader (YAML + environment), dataclass-based configuration.
  - `localization.py`: TextPack definitions (Persian default, English) + language normalization.
  - `handlers/`
    - `dm.py`: DM flows (application form, admin panel, language menu, status). Uses safe HTML and analytics.
    - `group.py`: Group flows (XP tracking, cups, leaderboards, admin checks).
  - `services/`
    - `storage.py`: Encrypted JSON state, dataclass models, async save/load, SQLite backup, statistics.
    - `security.py`: Fernet-based EncryptionManager, RateLimitGuard (burst token bucket).
    - `analytics.py`: Async in-memory aggregator with periodic logging snapshots and a NullAnalytics no-op.
  - `ui/`
    - `keyboards.py`: Inline keyboards for DM/admin/leaderboards, using localization text packs.

Key entrypoints and configuration:
- Telegram bot: `python bot.py`
- Web app: `uvicorn webapp.server:app --host 0.0.0.0 --port 8080`
- Configuration file: `config/settings.yaml` (copy from example) and environment variables for secrets.

Separation of concerns:
- Handlers (presentation and interaction) vs services (business logic, storage, security) vs UI (keyboards) vs localization (content) vs web (HTTP API).

## 3. Test Strategy
- Framework: Pytest
  - Async tests use `asyncio.run(...)` or anyio fixture (`@pytest.mark.anyio("asyncio")`).
  - Mocks: `unittest.mock.AsyncMock`, `SimpleNamespace`, and monkeypatching for I/O (e.g., `aioopen`).
- Coverage targets (guidance):
  - Storage invariants: encryption, atomic writes, language-aware questions, XP/cups, statistics, SQLite export.
  - Handler flows: DM application multi-step, admin panel actions, language menu, group XP/cups, admin checks.
  - Security/escaping: HTML-escape any user-generated content before rendering with `ParseMode.HTML`.
- Structure & naming:
  - Tests live in `tests/` and follow `test_*.py` naming.
  - Use stubs/fixtures for Telegram objects; avoid real network calls. Prefer dependency injection or monkeypatch.
- Mocking guidelines:
  - Replace networked bot methods with `AsyncMock`.
  - Monkeypatch `aioopen` to simulate partial writes/failures; assert atomicity and cleanup of temp files.
  - Patch handler internals (e.g., `_resolve_leaderboard_names`) to avoid external I/O.
- Unit vs integration:
  - Unit tests for handlers and services without contacting Telegram/HTTP.
  - Web app endpoints can be covered with FastAPI test client if desired (not required for core bot logic).

## 4. Code Style
- Python & Async
  - Python 3.11+ style (PEP 604 unions `str | None`, `from __future__ import annotations`).
  - Prefer async functions; never block the event loop (no `time.sleep`). Use `await`, `asyncio` primitives, and `analytics.track_time`.
  - Use `AIORateLimiter` in ApplicationBuilder and a custom `RateLimitGuard` for DM flows.
- Typing & Data Models
  - Type hints across modules; dataclasses for state (`Application`, `ApplicationResponse`, `ApplicationHistoryEntry`, `StorageState`).
  - Keep models immutable where appropriate, but StorageState is mutable with an internal asyncio lock.
- Naming conventions
  - snake_case for functions/variables; PascalCase for classes; UPPER_CASE for module-level constants (e.g., `LOGGER`).
  - Prefix non-public helpers with `_` (e.g., `_render_application_text`).
- Documentation & comments
  - Concise docstrings where useful (e.g., `format_timestamp`, webapp helpers). Prefer readable code + logging over heavy comments.
- Error handling & logging
  - Wrap network/Telegram calls in try/except; log errors and continue (fail-safe UX).
  - In services, re-raise or return error states as needed; ensure atomic file writes with temp file and `os.replace`.
  - Use `HTTPException` in FastAPI endpoints for invalid operations (e.g., duplicate admins, not found).
- Internationalization
  - Use `get_text_pack` and `normalize_language_code` consistently.
  - Persist preferred language in `context.user_data` (DM) or `context.chat_data` (group).

## 5. Common Patterns
- Handler construction
  - Define a `.build_handlers()` returning python-telegram-bot handlers; keep DM and Group concerns separate.
  - Store temporary flow state in `context.user_data` keys like `is_filling_application`, `application_flow`, `pending_*`.
- Safe rendering
  - Always HTML-escape user content before sending with `ParseMode.HTML` (names, usernames, answers, notes, titles, descriptions).
- Application flow
  - Multi-step: role -> optional role follow-up -> goals -> availability.
  - Question overrides via `Storage.get_application_questions(language)` by IDs: `role_prompt`, `goals_prompt`, `availability_prompt`, `followup_{role}`.
  - Collapse structured responses for backward compatibility; store structured `responses` when available.
- Admin panel
  - Owner-only actions for promote/demote; admins can review applications and view members.
  - Use inline keyboards defined in `ui/keyboards.py` and localization strings.
- Storage
  - Encrypted JSON blob via Fernet; atomic writes using a temporary path then `os.replace`.
  - Optional SQLite backup for analytics/reporting; schema fully recreated on each export.
  - Statistics: status counts, language distribution, recent updates, average pending answer length.
- Analytics
  - Non-blocking queue aggregator with periodic flush to logs; context manager `track_time` measures operation durations.
- Rate limiting
  - `RateLimitGuard` token bucket per-user to prevent abuse in DM flows.
- WebApp
  - FastAPI app exposes read/write admin endpoints; dependencies inject `Settings` and `Storage`.
  - Static SPA reads JSON from `/api/...`, renders in Farsi by default.

## 6. Do's and Don'ts
- ✅ Do
  - Use `escape()` for any user-supplied string before sending HTML-formatted messages.
  - Wrap Telegram API calls in try/except; record analytics events on success and failure.
  - Use `Settings.load()` and environment variables; never hardcode tokens or keys.
  - Maintain handler separation (DM vs Group) and keep UI creation in `ui/keyboards.py`.
  - Hold the storage lock for all mutating operations; call `await storage.save()` via service methods, not ad hoc.
  - Respect language preferences and update `context.user_data` or `context.chat_data` accordingly.
  - Keep callback_data patterns stable (e.g., `admin_panel:*`, `application:*`, `leaderboard:*`).
  - Ensure every new user-visible string is added to all TextPacks (FA/EN) with consistent keys.
  - Validate and normalize inputs (strip usernames, lstrip '@', normalize language codes).
- ❌ Don't
  - Don’t insert unescaped user content into HTML messages.
  - Don’t block the event loop or perform CPU-heavy work in handlers.
  - Don’t bypass Storage for state mutations or write files directly from handlers.
  - Don’t assume Telegram objects are present; check for `None` (e.g., `effective_chat`, `effective_user`).
  - Don’t introduce new TextPack fields in only one language.
  - Don’t leak secrets in logs; log metadata, not sensitive values.

## 7. Tools & Dependencies
- Core
  - python-telegram-bot[rate-limiter,callback-data]==20.7 — async bot engine, rate limiting, callback data support.
  - cryptography (Fernet) — encryption of storage payloads.
  - aiofiles — async file I/O for encrypted storage writes.
  - PyYAML — configuration parsing for `settings.yaml`.
  - FastAPI + Uvicorn — WebApp with static UI and JSON APIs.
  - pytest — unit testing, async support via anyio/asyncio.
  - uvloop (optional) — faster event loop on non-Windows platforms.
- Setup
  - `pip install -r requirements.txt`
  - Copy `config/settings.example.yaml` to `config/settings.yaml` and adjust.
  - Set environment variables: `BOT_TOKEN` (or custom per `telegram.bot_token_env`) and `BOT_SECRET_KEY` (or `telegram.secret_key_env`).
  - Run bot: `python bot.py`
  - Run webapp: `uvicorn webapp.server:app --host 0.0.0.0 --port 8080`
  - Tests: `pytest`

## 8. Other Notes
- Localization
  - Persian is the default language; English is available. When adding features, update both packs and language names where necessary.
- Storage compatibility
  - `normalize_timestamp` preserves readability for legacy ISO values; avoid changing timestamp formats without migration.
  - The SQLite export is a derivative of the JSON snapshot; schema changes must be mirrored in both.
- Extending admin features
  - WebApp endpoints validate inputs with Pydantic models and return HTTP errors on conflicts; mirror this behavior in bot-side flows.
- HTML rendering
  - When composing messages, prefer small, predictable templates and keep all interpolations escaped. The tests assert escaping behavior.
- LLM guidance
  - Reuse existing helpers (escaping, language resolution, keyboards, analytics).
  - Keep callback_data grammars consistent; new actions should follow `namespace:action[:arg]` convention.
  - Use `NullAnalytics` when analytics is optional, and don’t break the `track_time` context manager semantics.
