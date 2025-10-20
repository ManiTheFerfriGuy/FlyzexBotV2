from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aiofiles import open as aioopen

from .xp import calculate_level_progress


LOGGER = logging.getLogger(__name__)


# Default local timezone (can be overridden at runtime via configure_timezone)
LOCAL_TIMEZONE = timezone(timedelta(hours=3, minutes=30))


def configure_timezone(tz_spec: str | None) -> None:
    """Configure the module's local timezone from a specification.

    Accepted formats:
    - "UTC+03:30" or "UTC-04:00"
    - "UTC" (treated as zero offset)

    If the value is invalid or None, the default is preserved.
    """
    global LOCAL_TIMEZONE
    if not tz_spec:
        return
    spec = str(tz_spec).strip().upper()
    if spec == "UTC":
        LOCAL_TIMEZONE = timezone(timedelta(0))
        return
    m = re.fullmatch(r"UTC([+-])(\d{1,2}):(\d{2})", spec)
    if not m:
        return
    sign, hh, mm = m.groups()
    hours = int(hh)
    minutes = int(mm)
    if hours > 23 or minutes > 59:
        return
    total = hours * 60 + minutes
    if sign == "-":
        total = -total
    LOCAL_TIMEZONE = timezone(timedelta(minutes=total))


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Return a compact, human-friendly timestamp in the local timezone."""

    moment = dt or datetime.now(LOCAL_TIMEZONE)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=LOCAL_TIMEZONE)
    moment = moment.astimezone(LOCAL_TIMEZONE)

    date_part = moment.strftime("%Y/%m/%d · %H:%M:%S")
    offset = moment.utcoffset()
    if not offset:
        return f"{date_part} UTC"

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{date_part} UTC{sign}{hours:02d}:{minutes:02d}"


def normalize_timestamp(value: str) -> str:
    """Convert legacy ISO timestamps to the modern display format."""

    if not value:
        return ""

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
    return format_timestamp(parsed)


@dataclass
class ApplicationResponse:
    question_id: str
    question: str
    answer: str


@dataclass
class Application:
    user_id: int
    full_name: str
    username: Optional[str]
    answer: Optional[str]
    created_at: str
    language_code: Optional[str] = None
    responses: List[ApplicationResponse] = field(default_factory=list)


@dataclass
class ApplicationHistoryEntry:
    status: str
    updated_at: str
    note: Optional[str] = None
    language_code: Optional[str] = None


@dataclass
class StorageState:
    admins: List[int] = field(default_factory=list)
    admin_profiles: Dict[int, Dict[str, Optional[str]]] = field(default_factory=dict)
    applications: Dict[int, Application] = field(default_factory=dict)
    application_history: Dict[int, ApplicationHistoryEntry] = field(default_factory=dict)
    xp: Dict[str, Dict[str, int]] = field(default_factory=dict)
    xp_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cups: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    application_questions: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "admins": self.admins,
            "admin_profiles": {
                str(user_id): {
                    key: value
                    for key, value in profile.items()
                    if value is not None
                }
                for user_id, profile in self.admin_profiles.items()
            },
            "applications": {
                str(k): {
                    **vars(v),
                    "responses": [vars(response) for response in v.responses],
                }
                for k, v in self.applications.items()
            },
            "application_history": {
                str(k): vars(v) for k, v in self.application_history.items()
            },
            "xp": self.xp,
            "xp_profiles": {
                str(user_id): {
                    key: value
                    for key, value in profile.items()
                    if value not in (None, "")
                }
                for user_id, profile in self.xp_profiles.items()
            },
            "cups": self.cups,
            "application_questions": {
                str(language): {
                    str(question_id): prompt
                    for question_id, prompt in questions.items()
                }
                for language, questions in self.application_questions.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "StorageState":
        applications = {}
        for key, value in payload.get("applications", {}).items():
            responses_payload = [
                ApplicationResponse(**response)
                for response in value.get("responses", [])
                if {"question_id", "question", "answer"}.issubset(response.keys())
            ]
            applications[int(key)] = Application(
                user_id=value["user_id"],
                full_name=value.get("full_name", ""),
                username=value.get("username"),
                answer=value.get("answer"),
                created_at=normalize_timestamp(value.get("created_at", "")),
                language_code=value.get("language_code"),
                responses=responses_payload,
            )

        application_history = {}
        for key, value in payload.get("application_history", {}).items():
            application_history[int(key)] = ApplicationHistoryEntry(
                status=value.get("status", ""),
                updated_at=normalize_timestamp(value.get("updated_at", "")),
                note=value.get("note"),
                language_code=value.get("language_code"),
            )
        return cls(
            admins=list(payload.get("admins", [])),
            admin_profiles={
                int(user_id): {
                    key: value
                    for key, value in (profile or {}).items()
                    if isinstance(value, str) and value
                }
                for user_id, profile in payload.get("admin_profiles", {}).items()
            },
            applications=applications,
            application_history=application_history,
            xp={k: {user: int(score) for user, score in v.items()} for k, v in payload.get("xp", {}).items()},
            xp_profiles={
                str(user_id): {
                    "username": profile.get("username"),
                    "full_name": profile.get("full_name"),
                    "updated_at": profile.get("updated_at"),
                    "last_chat": profile.get("last_chat"),
                    "chats": [str(chat) for chat in profile.get("chats", []) if chat],
                }
                for user_id, profile in payload.get("xp_profiles", {}).items()
                if isinstance(profile, dict)
            },
            cups={
                k: [
                    {
                        **entry,
                        "created_at": normalize_timestamp(entry.get("created_at", "")),
                    }
                    for entry in v
                ]
                for k, v in payload.get("cups", {}).items()
            },
            application_questions={
                str(language): {
                    str(question_id): str(prompt)
                    for question_id, prompt in (questions or {}).items()
                    if isinstance(question_id, str)
                    and isinstance(prompt, str)
                    and prompt.strip()
                }
                for language, questions in payload.get("application_questions", {}).items()
                if isinstance(language, str)
            },
        )


class Storage:
    _DEFAULT_LANGUAGE_KEY = "__default__"

    def __init__(
        self,
        path: Path,
        *,
        backup_path: Optional[Path] = None,
    ) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._state = StorageState()
        self._backup_path = backup_path
        self._persistence_enabled = True
        self._snapshot_signature: tuple[float, int] | None = None

    def disable_persistence(self) -> None:
        """Disable load/save operations for ephemeral runtimes."""

        self._persistence_enabled = False
        self._backup_path = None
        self._snapshot_signature = None

    def _compute_snapshot_signature(self) -> tuple[float, int] | None:
        """Return a tuple describing the on-disk snapshot, if present."""

        try:
            stat = self._path.stat()
        except FileNotFoundError:
            return None
        return (stat.st_mtime, stat.st_size)

    async def load(self) -> None:
        if not self._persistence_enabled:
            return

        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._state = StorageState()
            self._snapshot_signature = None
            return

        async with aioopen(self._path, "rb") as file:
            payload_bytes = await file.read()

        if not payload_bytes:
            return

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            LOGGER.exception(
                "storage_load_failed", extra={"path": str(self._path)}
            )
            return

        self._state = StorageState.from_dict(payload)
        self._snapshot_signature = self._compute_snapshot_signature()
        LOGGER.info("storage_loaded", extra={"path": str(self._path)})

    async def save(self) -> None:
        if not self._persistence_enabled:
            return

        payload = await self._snapshot()
        await self._write_snapshot(payload)
        if self._backup_path:
            try:
                await self._write_sqlite_backup(payload)
            except Exception:
                LOGGER.exception(
                    "sqlite_backup_failed", extra={"path": str(self._backup_path)}
                )
        self._snapshot_signature = self._compute_snapshot_signature()

    async def ensure_latest_snapshot(self) -> None:
        """Reload state from disk when an updated snapshot is detected."""

        if not self._persistence_enabled:
            return

        async with self._lock:
            signature = self._compute_snapshot_signature()
            if signature == self._snapshot_signature:
                return

            if signature is None:
                if self._snapshot_signature is not None:
                    self._state = StorageState()
                self._snapshot_signature = None
                return

            await self.load()

    async def add_admin(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> bool:
        normalized_username = username.strip() if isinstance(username, str) else None
        if normalized_username:
            normalized_username = normalized_username.lstrip("@") or None

        normalized_full_name = full_name.strip() if isinstance(full_name, str) else None
        async with self._lock:
            profile = self._state.admin_profiles.setdefault(user_id, {})
            changed = False

            if user_id not in self._state.admins:
                self._state.admins.append(user_id)
                changed = True

            if normalized_username and profile.get("username") != normalized_username:
                profile["username"] = normalized_username
                changed = True

            if normalized_full_name and profile.get("full_name") != normalized_full_name:
                profile["full_name"] = normalized_full_name
                changed = True

            if not profile:
                self._state.admin_profiles.pop(user_id, None)

            if not changed:
                return False

        await self.save()
        LOGGER.info("admin_added", extra={"user_id": user_id})
        return True

    async def remove_admin(self, user_id: int) -> bool:
        async with self._lock:
            if user_id not in self._state.admins:
                return False
            self._state.admins.remove(user_id)
            self._state.admin_profiles.pop(user_id, None)
        await self.save()
        LOGGER.info("admin_removed", extra={"user_id": user_id})
        return True

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._state.admins

    def list_admins(self) -> List[int]:
        return list(self._state.admins)

    def get_admin_details(self) -> List[Dict[str, Optional[str]]]:
        details: List[Dict[str, Optional[str]]] = []
        for admin_id in self._state.admins:
            profile = self._state.admin_profiles.get(admin_id, {})
            username = profile.get("username")
            full_name = profile.get("full_name")

            application = self._state.applications.get(admin_id)
            if application:
                username = username or application.username
                full_name = full_name or application.full_name

            details.append(
                {
                    "user_id": admin_id,
                    "username": username,
                    "full_name": full_name,
                }
            )
        return details

    def get_admin_profile(self, user_id: int) -> Optional[Dict[str, Optional[str]]]:
        if user_id not in self._state.admins:
            return None

        profile = dict(self._state.admin_profiles.get(user_id, {}))
        username = profile.get("username")
        full_name = profile.get("full_name")

        application = self._state.applications.get(user_id)
        if application:
            username = username or application.username
            full_name = full_name or application.full_name

        xp_profile = self._state.xp_profiles.get(str(user_id))
        if xp_profile:
            username = username or xp_profile.get("username")
            full_name = full_name or xp_profile.get("full_name")

        return {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
        }

    def get_any_profile(self, user_id: int) -> Dict[str, Optional[str]]:
        """Best-effort profile resolution for a user id from known storage.

        This consults admin_profiles first, then applications as a fallback.
        Missing fields are returned as None.
        """
        profile = dict(self._state.admin_profiles.get(user_id, {}))
        username = profile.get("username")
        full_name = profile.get("full_name")
        application = self._state.applications.get(user_id)
        if application:
            username = username or application.username
            full_name = full_name or application.full_name
        xp_profile = self._state.xp_profiles.get(str(user_id))
        if xp_profile:
            username = username or xp_profile.get("username")
            full_name = full_name or xp_profile.get("full_name")
        return {"username": username, "full_name": full_name}

    def get_profile_by_identifier(
        self, identifier: object
    ) -> Tuple[Optional[int], Dict[str, Optional[str]]]:
        """Resolve a profile using a numeric identifier or username."""

        if isinstance(identifier, int):
            return identifier, self.get_any_profile(identifier)

        if not isinstance(identifier, str):
            return None, {"username": None, "full_name": None}

        trimmed = identifier.strip()
        if not trimmed:
            return None, {"username": None, "full_name": None}

        try:
            user_id = int(trimmed)
        except ValueError:
            user_id = None

        if user_id is not None:
            return user_id, self.get_any_profile(user_id)

        return self._resolve_profile_by_username(trimmed)

    def _resolve_profile_by_username(
        self, username: str
    ) -> Tuple[Optional[int], Dict[str, Optional[str]]]:
        normalised = self._normalise_username(username)
        if not normalised:
            return None, {"username": None, "full_name": None}

        lookup = normalised.casefold()

        for user_id, profile in self._state.admin_profiles.items():
            stored = self._normalise_username(profile.get("username"))
            if stored and stored.casefold() == lookup:
                data = self.get_any_profile(user_id)
                if not data.get("username"):
                    data["username"] = stored
                return user_id, data

        for user_id, application in self._state.applications.items():
            stored = self._normalise_username(application.username)
            if stored and stored.casefold() == lookup:
                data = self.get_any_profile(user_id)
                if not data.get("username"):
                    data["username"] = stored
                if application.full_name and not data.get("full_name"):
                    data["full_name"] = application.full_name
                return user_id, data

        for raw_id, profile in self._state.xp_profiles.items():
            stored = self._normalise_username(profile.get("username"))
            if stored and stored.casefold() == lookup:
                full_name = profile.get("full_name")
                try:
                    numeric_id = int(raw_id)
                except (TypeError, ValueError):
                    numeric_id = None
                if numeric_id is not None:
                    data = self.get_any_profile(numeric_id)
                    if not data.get("username"):
                        data["username"] = stored
                    if full_name and not data.get("full_name"):
                        data["full_name"] = full_name
                    return numeric_id, data
                return None, {"username": stored, "full_name": full_name}

        return None, {"username": normalised, "full_name": None}

    def _normalise_username(self, username: Optional[str]) -> Optional[str]:
        if not isinstance(username, str):
            return None
        trimmed = username.strip()
        if not trimmed:
            return None
        trimmed = trimmed.lstrip("@").strip()
        if not trimmed:
            return None
        return trimmed

    def _normalise_language_key(self, language_code: Optional[str]) -> str:
        if language_code is None:
            return self._DEFAULT_LANGUAGE_KEY
        code = str(language_code).strip()
        if not code:
            return self._DEFAULT_LANGUAGE_KEY
        return code.lower()

    def get_application_questions(self, language_code: Optional[str] = None) -> Dict[str, str]:
        language_key = self._normalise_language_key(language_code)
        overrides: Dict[str, str] = {}
        default_bucket = self._state.application_questions.get(
            self._DEFAULT_LANGUAGE_KEY,
            {},
        )
        if default_bucket:
            overrides.update(default_bucket)
        if language_key != self._DEFAULT_LANGUAGE_KEY:
            overrides.update(
                self._state.application_questions.get(language_key, {})
            )
        return dict(overrides)

    async def set_application_question(
        self,
        question_id: str,
        prompt: Optional[str],
        *,
        language_code: Optional[str] = None,
    ) -> bool:
        normalised_id = (question_id or "").strip()
        if not normalised_id:
            return False

        trimmed_prompt = (prompt or "").strip()
        language_key = self._normalise_language_key(language_code)

        async with self._lock:
            bucket = self._state.application_questions.setdefault(language_key, {})
            if trimmed_prompt:
                if bucket.get(normalised_id) == trimmed_prompt:
                    return False
                bucket[normalised_id] = trimmed_prompt
            else:
                if normalised_id not in bucket:
                    return False
                bucket.pop(normalised_id, None)
                if not bucket:
                    self._state.application_questions.pop(language_key, None)

        await self.save()
        LOGGER.info(
            "application_question_updated",
            extra={"question_id": normalised_id, "language": language_key},
        )
        return True

    async def add_application(
        self,
        user_id: int,
        full_name: str,
        username: Optional[str],
        answer: Optional[str],
        language_code: Optional[str] = None,
        responses: Optional[List[ApplicationResponse]] = None,
    ) -> bool:
        async with self._lock:
            history_entry = self._state.application_history.get(user_id)
            if history_entry and history_entry.status == "approved":
                return False
            if user_id in self._state.applications:
                return False
            timestamp = format_timestamp()
            self._state.applications[user_id] = Application(
                user_id=user_id,
                full_name=full_name,
                username=username,
                answer=answer,
                created_at=timestamp,
                language_code=language_code,
                responses=list(responses or []),
            )
            self._state.application_history[user_id] = ApplicationHistoryEntry(
                status="pending",
                updated_at=timestamp,
                language_code=language_code,
            )
        await self.save()
        LOGGER.info("application_added", extra={"user_id": user_id})
        return True

    def has_application(self, user_id: int) -> bool:
        return user_id in self._state.applications

    def get_application(self, user_id: int) -> Optional[Application]:
        return self._state.applications.get(user_id)

    async def pop_application(self, user_id: int) -> Optional[Application]:
        async with self._lock:
            application = self._state.applications.pop(user_id, None)
        if application:
            await self.save()
        return application

    def get_pending_applications(self) -> List[Application]:
        return list(self._state.applications.values())

    async def withdraw_application(self, user_id: int) -> bool:
        async with self._lock:
            application = self._state.applications.pop(user_id, None)
            if not application:
                return False
            timestamp = format_timestamp()
            self._state.application_history[user_id] = ApplicationHistoryEntry(
                status="withdrawn",
                updated_at=timestamp,
                language_code=getattr(application, "language_code", None),
            )
        await self.save()
        LOGGER.info("application_withdrawn", extra={"user_id": user_id})
        return True

    async def mark_application_status(
        self,
        user_id: int,
        status: str,
        note: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> None:
        async with self._lock:
            timestamp = format_timestamp()
            previous = self._state.application_history.get(user_id)
            language = language_code or getattr(previous, "language_code", None)
            self._state.application_history[user_id] = ApplicationHistoryEntry(
                status=status,
                updated_at=timestamp,
                note=note,
                language_code=language,
            )
        await self.save()
        LOGGER.info("application_status_updated", extra={"user_id": user_id, "status": status})

    def get_application_status(self, user_id: int) -> Optional[ApplicationHistoryEntry]:
        return self._state.application_history.get(user_id)

    def get_applicants_by_status(self, status: str) -> List[tuple[int, ApplicationHistoryEntry]]:
        return [
            (user_id, history)
            for user_id, history in self._state.application_history.items()
            if history.status == status
        ]

    def get_application_statistics(self) -> Dict[str, Any]:
        history = list(self._state.application_history.items())
        status_counter = Counter(entry.status for _, entry in history)
        language_counter = Counter(
            (entry.language_code or "unknown") for _, entry in history if entry.language_code
        )
        for application in self._state.applications.values():
            code = application.language_code or "unknown"
            language_counter[code] += 1

        pending_lengths = [
            sum(len(response.answer) for response in application.responses)
            or len(application.answer or "")
            for application in self._state.applications.values()
        ]
        average_response_length = (
            sum(pending_lengths) / len(pending_lengths)
            if pending_lengths
            else 0
        )

        recent_updates = sorted(
            history,
            key=lambda item: getattr(item[1], "updated_at", ""),
            reverse=True,
        )[:5]

        return {
            "total": len(history),
            "pending": len(self._state.applications),
            "status_counts": dict(status_counter),
            "languages": dict(language_counter),
            "average_pending_answer_length": average_response_length,
            "recent_updates": [
                {
                    "user_id": user_id,
                    "status": entry.status,
                    "updated_at": entry.updated_at,
                }
                for user_id, entry in recent_updates
            ],
        }

    async def add_xp(
        self,
        chat_id: int,
        user_id: int,
        amount: int,
        *,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> int:
        async with self._lock:
            chat_key = str(chat_id)
            user_key = str(user_id)
            self._state.xp.setdefault(chat_key, {})
            self._state.xp[chat_key][user_key] = self._state.xp[chat_key].get(user_key, 0) + amount

            profile = self._state.xp_profiles.setdefault(user_key, {})
            normalized_username = username.strip() if isinstance(username, str) else None
            if normalized_username:
                normalized_username = normalized_username.lstrip("@") or None
            normalized_full_name = full_name.strip() if isinstance(full_name, str) else None

            if normalized_username:
                profile["username"] = normalized_username
            if normalized_full_name:
                profile["full_name"] = normalized_full_name

            chats = profile.setdefault("chats", [])
            if str(chat_key) not in chats:
                chats.append(str(chat_key))
            now = datetime.now(LOCAL_TIMEZONE)
            profile["last_chat"] = chat_key
            profile["updated_at"] = format_timestamp(now)
            profile["updated_at_iso"] = now.isoformat()

        await self.save()
        LOGGER.debug(
            "xp_added",
            extra={
                "chat_id": chat_id,
                "user_id": user_id,
                "amount": amount,
                "username": username,
            },
        )
        return self._state.xp[chat_key][user_key]

    def get_xp_leaderboard(self, chat_id: int, limit: int) -> List[tuple[str, int]]:
        chat_key = str(chat_id)
        scores = self._state.xp.get(chat_key, {})
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_scores[:limit]

    def get_user_xp(self, chat_id: int, user_id: int) -> Optional[int]:
        chat_scores = self._state.xp.get(str(chat_id))
        if not chat_scores:
            return None
        value = chat_scores.get(str(user_id))
        try:
            return int(str(value))
        except Exception:
            return None

    def get_xp_profile(self, user_id: int | str) -> Optional[Dict[str, Any]]:
        profile = self._state.xp_profiles.get(str(user_id))
        if profile is None:
            return None
        return dict(profile)

    def get_group_snapshot(self, chat_id: int) -> Dict[str, Any]:
        chat_key = str(chat_id)
        scores = self._state.xp.get(chat_key, {}) or {}

        members_tracked = 0
        total_xp = 0
        top_pair: Optional[Tuple[str, int]] = None
        for user_key, raw_value in scores.items():
            try:
                value_int = int(raw_value)
            except Exception:
                continue
            members_tracked += 1
            total_xp += value_int
            if top_pair is None or value_int > top_pair[1]:
                top_pair = (str(user_key), value_int)

        top_member: Optional[Dict[str, Any]] = None
        if top_pair is not None:
            user_key, xp_value = top_pair
            progress = calculate_level_progress(xp_value)
            profile = self._state.xp_profiles.get(user_key, {})
            display_name = (
                profile.get("full_name")
                or profile.get("username")
                or user_key
            )
            try:
                resolved_id = int(user_key)
            except Exception:
                resolved_id = user_key
            top_member = {
                "user_id": resolved_id,
                "display": display_name,
                "xp": xp_value,
                "level": progress.level,
            }

        cups = list(self._state.cups.get(chat_key, []))
        cup_count = len(cups)
        recent_cup: Optional[Dict[str, Any]] = None
        if cups:
            latest = max(cups, key=lambda item: item.get("created_at") or "")
            recent_cup = {
                "title": latest.get("title", ""),
                "created_at": latest.get("created_at"),
            }

        admins_tracked = len(self._state.admins)

        latest_activity_display: Optional[str] = None
        latest_activity_dt: Optional[datetime] = None
        for profile in self._state.xp_profiles.values():
            chats = profile.get("chats", []) or []
            if chat_key not in chats:
                continue
            iso_value = profile.get("updated_at_iso")
            if not iso_value:
                continue
            try:
                candidate = datetime.fromisoformat(str(iso_value))
            except ValueError:
                continue
            if latest_activity_dt is None or candidate > latest_activity_dt:
                latest_activity_dt = candidate
                latest_activity_display = format_timestamp(candidate)

        if latest_activity_display is None:
            for profile in self._state.xp_profiles.values():
                chats = profile.get("chats", []) or []
                if chat_key not in chats:
                    continue
                candidate_display = profile.get("updated_at")
                if candidate_display:
                    latest_activity_display = str(candidate_display)
                    break

        return {
            "members_tracked": members_tracked,
            "total_xp": total_xp,
            "top_member": top_member,
            "cup_count": cup_count,
            "recent_cup": recent_cup,
            "admins_tracked": admins_tracked,
            "last_activity": latest_activity_display,
        }

    def get_global_xp_top(self, limit: int) -> List[tuple[str, int]]:
        """Aggregate XP across all chats and return top N users (by total XP)."""
        totals: Dict[str, int] = {}
        for chat_scores in self._state.xp.values():
            for user_id, score in chat_scores.items():
                totals[user_id] = totals.get(user_id, 0) + int(score)
        return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]

    def get_cup_wins_top(self, limit: int) -> List[tuple[str, int]]:
        """Estimate cup wins by counting numeric user ids in podium lists across chats.

        Entries that cannot be parsed as integer user ids are ignored.
        """
        wins: Dict[str, int] = {}
        for cup_list in self._state.cups.values():
            for cup in cup_list:
                for entry in cup.get("podium", []) or []:
                    try:
                        uid = str(int(str(entry).strip()))
                    except Exception:
                        continue
                    wins[uid] = wins.get(uid, 0) + 1
        return sorted(wins.items(), key=lambda item: item[1], reverse=True)[:limit]

    async def add_cup(self, chat_id: int, title: str, description: str, podium: List[str]) -> None:
        async with self._lock:
            chat_key = str(chat_id)
            self._state.cups.setdefault(chat_key, [])
            self._state.cups[chat_key].append(
                {
                    "title": title,
                    "description": description,
                    "podium": podium,
                    "created_at": format_timestamp(),
                }
            )
        await self.save()
        LOGGER.info("cup_added", extra={"chat_id": chat_id, "title": title})

    def get_cups(self, chat_id: int, limit: int) -> List[Dict[str, Any]]:
        chat_key = str(chat_id)
        cups = self._state.cups.get(chat_key, [])
        cups_sorted = sorted(cups, key=lambda item: item["created_at"], reverse=True)
        return cups_sorted[:limit]

    async def _snapshot(self) -> bytes:
        async with self._lock:
            payload = json.dumps(self._state.to_dict()).encode("utf-8")
        return payload

    async def _write_snapshot(self, payload: bytes) -> None:
        to_write = payload
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if self._path.suffix:
            tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        else:
            tmp_path = self._path.with_name(self._path.name + ".tmp")

        try:
            async with aioopen(tmp_path, "wb") as file:
                await file.write(to_write)
                await file.flush()
            await asyncio.to_thread(os.replace, tmp_path, self._path)
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                await asyncio.to_thread(tmp_path.unlink)
            raise

        LOGGER.debug("storage_flushed", extra={"path": str(self._path)})

    async def _write_sqlite_backup(self, payload: bytes) -> None:
        if not self._backup_path:
            return

        snapshot = json.loads(payload.decode("utf-8"))
        await asyncio.to_thread(self._dump_sqlite_backup, snapshot)

    def _dump_sqlite_backup(self, snapshot: Dict[str, Any]) -> None:
        assert self._backup_path is not None
        self._backup_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._backup_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.cursor()

            cursor.executescript(
                """
                DROP TABLE IF EXISTS admins;
                DROP TABLE IF EXISTS admin_profiles;
                DROP TABLE IF EXISTS applications;
                DROP TABLE IF EXISTS application_responses;
                DROP TABLE IF EXISTS application_history;
                DROP TABLE IF EXISTS xp;
                DROP TABLE IF EXISTS cups;
                DROP TABLE IF EXISTS application_questions;
                DROP TABLE IF EXISTS metadata;

                CREATE TABLE admins (
                    user_id INTEGER PRIMARY KEY
                );

                CREATE TABLE admin_profiles (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT
                );

                CREATE TABLE applications (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    username TEXT,
                    answer TEXT,
                    created_at TEXT,
                    language_code TEXT
                );

                CREATE TABLE application_responses (
                    user_id INTEGER,
                    position INTEGER,
                    question_id TEXT,
                    question TEXT,
                    answer TEXT,
                    PRIMARY KEY (user_id, position),
                    FOREIGN KEY (user_id) REFERENCES applications(user_id) ON DELETE CASCADE
                );

                CREATE TABLE application_history (
                    user_id INTEGER PRIMARY KEY,
                    status TEXT,
                    updated_at TEXT,
                    note TEXT,
                    language_code TEXT,
                    FOREIGN KEY (user_id) REFERENCES applications(user_id) ON DELETE CASCADE
                );

                CREATE TABLE xp (
                    chat_id TEXT,
                    user_id TEXT,
                    score INTEGER,
                    PRIMARY KEY (chat_id, user_id)
                );

                CREATE TABLE cups (
                    chat_id TEXT,
                    position INTEGER,
                    title TEXT,
                    description TEXT,
                    podium TEXT,
                    created_at TEXT,
                    PRIMARY KEY (chat_id, position)
                );

                CREATE TABLE application_questions (
                    language_code TEXT,
                    question_id TEXT,
                    prompt TEXT,
                    PRIMARY KEY (language_code, question_id)
                );

                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )

            admins = [(int(user_id),) for user_id in snapshot.get("admins", [])]
            if admins:
                cursor.executemany("INSERT INTO admins(user_id) VALUES (?)", admins)

            profiles = [
                (
                    int(user_id),
                    profile.get("username"),
                    profile.get("full_name"),
                )
                for user_id, profile in snapshot.get("admin_profiles", {}).items()
            ]
            if profiles:
                cursor.executemany(
                    "INSERT INTO admin_profiles(user_id, username, full_name) VALUES (?, ?, ?)",
                    profiles,
                )

            applications = []
            responses: List[tuple[int, int, Optional[str], Optional[str], Optional[str]]] = []
            for user_id, application in snapshot.get("applications", {}).items():
                int_user_id = int(user_id)
                applications.append(
                    (
                        int_user_id,
                        application.get("full_name"),
                        application.get("username"),
                        application.get("answer"),
                        application.get("created_at"),
                        application.get("language_code"),
                    )
                )
                for position, response in enumerate(application.get("responses", [])):
                    responses.append(
                        (
                            int_user_id,
                            position,
                            response.get("question_id"),
                            response.get("question"),
                            response.get("answer"),
                        )
                    )

            if applications:
                cursor.executemany(
                    """
                    INSERT INTO applications(
                        user_id, full_name, username, answer, created_at, language_code
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    applications,
                )

            if responses:
                cursor.executemany(
                    """
                    INSERT INTO application_responses(
                        user_id, position, question_id, question, answer
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    responses,
                )

            history_rows = [
                (
                    int(user_id),
                    entry.get("status"),
                    entry.get("updated_at"),
                    entry.get("note"),
                    entry.get("language_code"),
                )
                for user_id, entry in snapshot.get("application_history", {}).items()
            ]
            if history_rows:
                cursor.executemany(
                    """
                    INSERT INTO application_history(
                        user_id, status, updated_at, note, language_code
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    history_rows,
                )

            xp_rows = [
                (chat_id, user_id, int(score))
                for chat_id, scores in snapshot.get("xp", {}).items()
                for user_id, score in scores.items()
            ]
            if xp_rows:
                cursor.executemany(
                    "INSERT INTO xp(chat_id, user_id, score) VALUES (?, ?, ?)", xp_rows
                )

            cups_rows = []
            for chat_id, cups in snapshot.get("cups", {}).items():
                for position, cup in enumerate(cups):
                    cups_rows.append(
                        (
                            chat_id,
                            position,
                            cup.get("title"),
                            cup.get("description"),
                            json.dumps(cup.get("podium", []), ensure_ascii=False),
                            cup.get("created_at"),
                        )
                    )
            if cups_rows:
                cursor.executemany(
                    """
                    INSERT INTO cups(
                        chat_id, position, title, description, podium, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    cups_rows,
                )

            question_rows = [
                (language, question_id, prompt)
                for language, questions in snapshot.get("application_questions", {}).items()
                for question_id, prompt in questions.items()
            ]
            if question_rows:
                cursor.executemany(
                    """
                    INSERT INTO application_questions(language_code, question_id, prompt)
                    VALUES (?, ?, ?)
                    """,
                    question_rows,
                )

            cursor.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("raw_snapshot", json.dumps(snapshot, ensure_ascii=False)),
            )
            cursor.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("exported_at", datetime.utcnow().isoformat()),
            )

