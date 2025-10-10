from __future__ import annotations

from html import escape
import logging
import time
from typing import Dict, List, Sequence, Tuple

from telegram import ChatMember, ChatPermissions, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from ..localization import (AVAILABLE_LANGUAGE_CODES, PERSIAN_TEXTS, TextPack,
                            get_text_pack, normalize_language_code)
from ..services.analytics import AnalyticsTracker, NullAnalytics
from ..services.storage import Storage
from ..ui.keyboards import (group_admin_panel_keyboard,
                            leaderboard_refresh_keyboard)

LOGGER = logging.getLogger(__name__)


class GroupHandlers:
    def __init__(
        self,
        storage: Storage,
        xp_reward: int,
        xp_limit: int,
        cups_limit: int,
        milestone_interval: int = 5,
        xp_notification_cooldown: int = 180,
        analytics: AnalyticsTracker | NullAnalytics | None = None,
    ) -> None:
        self.storage = storage
        self.xp_reward = xp_reward
        self.xp_limit = xp_limit
        self.cups_limit = cups_limit
        self.milestone_interval = milestone_interval
        self.analytics = analytics or NullAnalytics()
        self.xp_notification_cooldown = max(0, xp_notification_cooldown)
        self._xp_notifications: Dict[Tuple[int, int], float] = {}

    def build_handlers(self) -> list:
        return [
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
                self.track_activity,
            ),
            CommandHandler("help", self.command_help, filters=filters.ChatType.GROUPS),
            CommandHandler("myxp", self.command_my_xp, filters=filters.ChatType.GROUPS),
            CommandHandler("xp", self.show_xp_leaderboard, filters=filters.ChatType.GROUPS),
            CommandHandler("cups", self.show_cup_leaderboard, filters=filters.ChatType.GROUPS),
            CommandHandler("add_cup", self.add_cup, filters=filters.ChatType.GROUPS),
            CommandHandler("addxp", self.command_add_xp, filters=filters.ChatType.GROUPS),
            CommandHandler("promote", self.command_promote_admin, filters=filters.ChatType.GROUPS),
            CommandHandler("demote", self.command_demote_admin, filters=filters.ChatType.GROUPS),
            CommandHandler("panel", self.show_panel, filters=filters.ChatType.GROUPS),
            CallbackQueryHandler(self.handle_leaderboard_refresh, pattern=r"^leaderboard:"),
            CallbackQueryHandler(self.handle_panel_action, pattern=r"^group_panel:"),
        ]

    async def track_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        if message is None or update.effective_chat is None or update.effective_user is None:
            return
        if getattr(update.effective_user, "is_bot", False):
            return
        if await self._maybe_handle_panel_response(update, context):
            return
        if message.text and message.text.startswith("/"):
            return
        texts = self._get_texts(context, getattr(update.effective_user, "language_code", None))
        try:
            async with self.analytics.track_time("group.track_activity"):
                new_score = await self.storage.add_xp(
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    amount=self.xp_reward,
                    full_name=getattr(update.effective_user, "full_name", None),
                    username=getattr(update.effective_user, "username", None),
                )
        except Exception as exc:
            LOGGER.error("Failed to update XP for %s: %s", update.effective_user.id, exc)
            await self.analytics.record("group.activity_error")
            return
        if self.xp_reward <= 0 or self.milestone_interval <= 0:
            await self.analytics.record("group.activity_tracked")
            return
        milestone_score = self.xp_reward * self.milestone_interval
        if milestone_score > 0 and new_score % milestone_score == 0:
            should_notify = True
            if self.xp_notification_cooldown:
                key = (update.effective_chat.id, update.effective_user.id)
                last_tick = self._xp_notifications.get(key, 0.0)
                now = time.monotonic()
                if now - last_tick < self.xp_notification_cooldown:
                    should_notify = False
                else:
                    self._xp_notifications[key] = now
            if should_notify:
                await message.reply_text(
                    texts.group_xp_updated.format(
                        full_name=update.effective_user.full_name
                        or update.effective_user.username
                        or str(update.effective_user.id),
                        xp=new_score,
                    )
                )
        await self.analytics.record("group.activity_tracked")

    async def command_add_xp(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        actor = update.effective_user
        message = update.effective_message
        if chat is None or actor is None or message is None:
            return
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        if not await self._is_admin(context, chat.id, actor.id):
            await message.reply_text(texts.dm_admin_only)
            return

        target_user = self._resolve_target_from_message(message)
        amount: int | None = None
        if context.args:
            try:
                amount = int(context.args[-1])
            except ValueError:
                amount = None
        if target_user is None and context.args:
            candidate = context.args[0]
            fetched = await self._fetch_member(context, chat.id, candidate)
            if fetched:
                target_user = fetched
        if target_user is None and message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
        if target_user is None or amount is None:
            await message.reply_text(texts.group_add_xp_usage)
            return

        try:
            total = await self.storage.add_xp(
                chat.id,
                target_user.id,
                amount,
                full_name=getattr(target_user, "full_name", None),
                username=getattr(target_user, "username", None),
            )
        except Exception as exc:
            LOGGER.error("Failed to grant XP manually: %s", exc)
            await message.reply_text(texts.error_generic)
            return

        await message.reply_text(
            texts.group_add_xp_success.format(
                full_name=target_user.full_name or target_user.username or target_user.id,
                xp=total,
            )
        )

    async def command_promote_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._handle_admin_toggle(update, context, promote=True)

    async def command_demote_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._handle_admin_toggle(update, context, promote=False)

    async def command_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        actor = update.effective_user
        message = update.effective_message
        if chat is None or actor is None or message is None:
            return
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        include_admin = False
        try:
            include_admin = await self._is_admin(context, chat.id, actor.id)
        except Exception:
            include_admin = False
        help_text = self._build_help_text(texts, include_admin=include_admin)
        await message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await self.analytics.record("group.help_requested")

    async def command_my_xp(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        actor = update.effective_user
        message = update.effective_message
        if chat is None or actor is None or message is None:
            return
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        xp_value = self.storage.get_user_xp(chat.id, actor.id)
        if xp_value is None:
            await message.reply_text(texts.group_myxp_no_data)
            await self.analytics.record("group.my_xp_requested")
            return
        display = escape(
            getattr(actor, "full_name", None)
            or getattr(actor, "username", None)
            or str(actor.id)
        )
        response = texts.group_myxp_response.format(full_name=display, xp=xp_value)
        await message.reply_text(response, parse_mode=ParseMode.HTML)
        await self.analytics.record("group.my_xp_requested")

    async def show_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        actor = update.effective_user
        message = update.effective_message
        if chat is None or actor is None or message is None:
            return
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        if not await self._is_admin(context, chat.id, actor.id):
            await message.reply_text(texts.dm_admin_only)
            return

        panel_text, markup = self._compose_group_panel(chat, texts)
        await message.reply_text(
            panel_text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        await self.analytics.record("group.panel_opened")

    async def handle_panel_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data:
            return
        user = query.from_user
        message = query.message
        chat = message.chat if message else None
        if chat is None or user is None:
            return
        if not await self._is_admin(context, chat.id, user.id):
            await query.answer()
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        await query.answer()
        _, action = query.data.split(":", 1)
        if action == "close":
            if message:
                try:
                    await message.edit_text(texts.group_panel_closed)
                except Exception:
                    await message.reply_text(texts.group_panel_closed)
            return

        if action == "refresh":
            if message:
                panel_text, markup = self._compose_group_panel(chat, texts)
                try:
                    await message.edit_text(
                        panel_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=markup,
                    )
                except Exception:
                    await message.reply_text(
                        panel_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=markup,
                    )
            await self.analytics.record("group.panel_refreshed")
            return

        if action == "help":
            help_text = self._build_help_text(texts, include_admin=True)
            if message:
                await message.reply_text(
                    help_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            await self.analytics.record("group.help_requested")
            return

        if action in {"ban", "mute", "add_xp"}:
            pending = context.chat_data.setdefault("group_panel_pending", {})
            pending[user.id] = {"action": action}
            prompt_key = {
                "ban": "group_panel_ban_prompt",
                "mute": "group_panel_mute_prompt",
                "add_xp": "group_panel_add_xp_prompt",
            }[action]
            await message.reply_text(getattr(texts, prompt_key))
            return

        info_messages = {
            "cups": texts.group_panel_cups_hint,
            "admins": texts.group_panel_admins_hint,
            "settings": texts.group_panel_settings_hint,
        }
        if action in info_messages:
            await message.reply_text(info_messages[action])

    async def show_xp_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat is None:
            return
        texts = self._get_texts(context, getattr(update.effective_user, "language_code", None))
        await self.analytics.record("group.xp_leaderboard_requested")
        text, mode, markup = await self._compose_xp_leaderboard(context, chat.id, texts)
        await chat.send_message(text, parse_mode=mode, reply_markup=markup)

    async def add_cup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        user = update.effective_user
        if chat is None or user is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        if not await self._is_admin(context, chat.id, user.id):
            await chat.send_message(texts.dm_admin_only)
            return
        if not context.args:
            await chat.send_message(texts.group_add_cup_usage)
            return

        raw = " ".join(context.args)
        # Parse "title | description | a,b,c" with basic validation and resilience
        parts = [part.strip() for part in raw.split("|", 2)]
        if len(parts) != 3:
            await chat.send_message(texts.group_add_cup_invalid_format)
            return
        title, description, podium_raw = parts
        if not title or not description:
            await chat.send_message(texts.group_add_cup_invalid_format)
            return
        # Reasonable limits to avoid overly long entries
        if len(title) > 100 or len(description) > 300:
            await chat.send_message(texts.group_add_cup_invalid_format)
            return
        podium = [slot.strip() for slot in podium_raw.split(",") if slot.strip()]
        # Limit podium size and entry length
        if len(podium) > 10 or any(len(entry) > 100 for entry in podium):
            await chat.send_message(texts.group_add_cup_invalid_format)
            return

        try:
            await self.storage.add_cup(chat.id, title, description, podium)
        except Exception as exc:
            LOGGER.error("Failed to add cup in chat %s: %s", chat.id, exc)
            await chat.send_message(texts.group_no_data)
            await self.analytics.record("group.cup_add_error")
            return
        await chat.send_message(texts.group_cup_added.format(title=title))
        await self.analytics.record("group.cup_added")

    async def show_cup_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat is None:
            return
        texts = self._get_texts(context, getattr(update.effective_user, "language_code", None))
        await self.analytics.record("group.cup_leaderboard_requested")
        text, mode, markup = self._compose_cup_leaderboard(chat.id, texts)
        await chat.send_message(text, parse_mode=mode, reply_markup=markup)

    async def handle_leaderboard_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()
        parts = query.data.split(":", 2)
        if len(parts) != 3:
            return
        _, board_type, chat_id_raw = parts
        message = query.message
        if message is None:
            return
        try:
            chat_id = int(chat_id_raw)
        except ValueError:
            return
        texts = self._get_texts(context, getattr(query.from_user, "language_code", None))
        if board_type == "xp":
            text, mode, markup = await self._compose_xp_leaderboard(context, chat_id, texts)
            await self.analytics.record("group.xp_leaderboard_refreshed")
        else:
            text, mode, markup = self._compose_cup_leaderboard(chat_id, texts)
            await self.analytics.record("group.cup_leaderboard_refreshed")
        await message.edit_text(text, parse_mode=mode, reply_markup=markup)

    def _build_help_text(self, texts: TextPack, *, include_admin: bool) -> str:
        lines: List[str] = [texts.group_help_intro, "", texts.group_help_member_title]
        member_commands = [
            ("/help", texts.group_help_cmd_help),
            ("/myxp", texts.group_help_cmd_myxp),
            ("/xp", texts.group_help_cmd_xp),
            ("/cups", texts.group_help_cmd_cups),
        ]
        for command, description in member_commands:
            lines.append(f"<b>{command}</b> — {description}")

        if include_admin:
            lines.extend(["", texts.group_help_admin_title, texts.group_help_admin_hint])
            admin_commands = [
                ("/panel", texts.group_help_cmd_panel),
                ("/add_cup", texts.group_help_cmd_add_cup),
                ("/addxp", texts.group_help_cmd_addxp),
                ("/promote", texts.group_help_cmd_promote),
                ("/demote", texts.group_help_cmd_demote),
            ]
            for command, description in admin_commands:
                lines.append(f"<b>{command}</b> — {description}")

        lines.extend(["", texts.group_help_footer])
        return "\n".join(lines).strip()

    def _compose_group_panel(self, chat, texts: TextPack) -> Tuple[str, InlineKeyboardMarkup]:
        snapshot = self.storage.get_group_snapshot(getattr(chat, "id", 0)) or {}
        chat_title_raw = (
            getattr(chat, "title", None)
            or getattr(chat, "full_name", None)
            or getattr(chat, "username", None)
            or texts.group_panel_unknown_chat
        )
        chat_title = escape(str(chat_title_raw))

        lines: List[str] = [
            texts.group_panel_intro.format(chat_title=chat_title),
            "",
            texts.group_panel_overview_title,
        ]

        metrics: List[str] = [
            texts.group_panel_metric_tracked.format(
                members=int(snapshot.get("members_tracked", 0))
            ),
            texts.group_panel_metric_total_xp.format(
                total_xp=int(snapshot.get("total_xp", 0))
            ),
        ]

        top_member = snapshot.get("top_member")
        if isinstance(top_member, dict) and top_member.get("display"):
            metrics.append(
                texts.group_panel_metric_top_member.format(
                    name=escape(str(top_member.get("display"))),
                    xp=int(top_member.get("xp", 0)),
                )
            )
        else:
            metrics.append(texts.group_panel_metric_top_member_empty)

        metrics.append(
            texts.group_panel_metric_cups.format(
                count=int(snapshot.get("cup_count", 0))
            )
        )
        metrics.append(
            texts.group_panel_metric_admins.format(
                count=int(snapshot.get("admins_tracked", 0))
            )
        )

        recent_cup = snapshot.get("recent_cup")
        if isinstance(recent_cup, dict) and recent_cup.get("title"):
            metrics.append(
                texts.group_panel_recent_cup.format(
                    title=escape(str(recent_cup.get("title"))),
                    created_at=recent_cup.get("created_at") or "—",
                )
            )

        last_activity = snapshot.get("last_activity")
        if last_activity:
            metrics.append(texts.group_panel_last_activity.format(timestamp=last_activity))

        lines.append("\n".join(metrics))
        lines.extend(["", texts.group_panel_actions_hint, texts.group_panel_help_hint])
        text = "\n".join(lines)
        markup = group_admin_panel_keyboard(texts)
        return (text, markup)

    async def _handle_admin_toggle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        promote: bool,
    ) -> None:
        chat = update.effective_chat
        actor = update.effective_user
        message = update.effective_message
        if chat is None or actor is None or message is None:
            return
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        if not await self._is_admin(context, chat.id, actor.id):
            await message.reply_text(texts.dm_admin_only)
            return

        target_user = self._resolve_target_from_message(message)
        if target_user is None and context.args:
            fetched = await self._fetch_member(context, chat.id, context.args[0])
            if fetched:
                target_user = fetched
        if target_user is None and message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
        if target_user is None:
            usage = texts.group_promote_usage if promote else texts.group_demote_usage
            await message.reply_text(usage)
            return

        try:
            if promote:
                changed = await self.storage.add_admin(
                    target_user.id,
                    username=getattr(target_user, "username", None),
                    full_name=getattr(target_user, "full_name", None),
                )
            else:
                changed = await self.storage.remove_admin(target_user.id)
        except Exception as exc:
            LOGGER.error("Failed to toggle admin: %s", exc)
            await message.reply_text(texts.error_generic)
            return

        if promote and not changed:
            await message.reply_text(texts.group_promote_already)
            return
        if not promote and not changed:
            await message.reply_text(texts.group_demote_missing)
            return

        confirmation = texts.group_promote_success if promote else texts.group_demote_success
        await message.reply_text(
            confirmation.format(
                full_name=target_user.full_name or target_user.username or target_user.id
            )
        )

    async def _maybe_handle_panel_response(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        message = update.effective_message
        chat = update.effective_chat
        actor = update.effective_user
        if message is None or chat is None or actor is None:
            return False
        pending_map = context.chat_data.get("group_panel_pending")
        if not isinstance(pending_map, dict) or actor.id not in pending_map:
            return False

        action = pending_map[actor.id]["action"]
        texts = self._get_texts(context, getattr(actor, "language_code", None))
        if message.text and message.text.lower().strip() == texts.group_panel_cancel_keyword:
            pending_map.pop(actor.id, None)
            await message.reply_text(texts.group_panel_cancelled)
            return True

        if action == "ban":
            target = self._resolve_target_from_message(message)
            if target is None:
                await message.reply_text(texts.group_panel_invalid_target)
                return True
            try:
                await context.bot.ban_chat_member(chat.id, target.id)
            except Exception as exc:
                LOGGER.error("Failed to ban %s: %s", target.id, exc)
                await message.reply_text(texts.group_panel_action_error)
                return True
            pending_map.pop(actor.id, None)
            await message.reply_text(
                texts.group_panel_ban_success.format(
                    full_name=target.full_name or target.username or target.id
                )
            )
            return True

        if action == "mute":
            target = self._resolve_target_from_message(message)
            if target is None:
                await message.reply_text(texts.group_panel_invalid_target)
                return True
            permissions = ChatPermissions(can_send_messages=False)
            try:
                await context.bot.restrict_chat_member(chat.id, target.id, permissions=permissions)
            except Exception as exc:
                LOGGER.error("Failed to mute %s: %s", target.id, exc)
                await message.reply_text(texts.group_panel_action_error)
                return True
            pending_map.pop(actor.id, None)
            await message.reply_text(
                texts.group_panel_mute_success.format(
                    full_name=target.full_name or target.username or target.id
                )
            )
            return True

        if action == "add_xp":
            target = self._resolve_target_from_message(message)
            if target is None:
                await message.reply_text(texts.group_panel_invalid_target)
                return True
            try:
                amount = int(message.text.strip())
            except (TypeError, ValueError):
                await message.reply_text(texts.group_add_xp_usage)
                return True
            try:
                total = await self.storage.add_xp(
                    chat.id,
                    target.id,
                    amount,
                    full_name=getattr(target, "full_name", None),
                    username=getattr(target, "username", None),
                )
            except Exception as exc:
                LOGGER.error("Failed to grant XP via panel: %s", exc)
                await message.reply_text(texts.error_generic)
                return True
            pending_map.pop(actor.id, None)
            await message.reply_text(
                texts.group_add_xp_success.format(
                    full_name=target.full_name or target.username or target.id,
                    xp=total,
                )
            )
            return True

        return False


    async def _is_admin(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
        try:
            member: ChatMember = await context.bot.get_chat_member(chat_id, user_id)
        except Exception as exc:
            LOGGER.error("Failed to fetch chat member: %s", exc)
            return False
        return member.status in {"administrator", "creator"} or self.storage.is_admin(user_id)

    async def _resolve_leaderboard_names(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        leaderboard: Sequence[Tuple[str, int]],
    ) -> List[Tuple[str, int]]:
        resolved: List[Tuple[str, int]] = []
        for user_id, xp in leaderboard:
            try:
                member = await context.bot.get_chat_member(chat_id, int(user_id))
                display = member.user.full_name or member.user.username or f"کاربر {user_id}"
            except Exception:
                display = f"کاربر {user_id}"
            resolved.append((display, xp))
        return resolved

    def _get_texts(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        language_code: str | None = None,
    ) -> TextPack:
        chat_data = getattr(context, "chat_data", None)
        stored_language: str | None = None
        stored_pack: TextPack | None = None
        if isinstance(chat_data, dict):
            maybe_stored = chat_data.get("preferred_language")
            if isinstance(maybe_stored, str):
                normalised_stored = normalize_language_code(maybe_stored) or maybe_stored
                if normalised_stored in AVAILABLE_LANGUAGE_CODES:
                    stored_language = normalised_stored
                    stored_pack = get_text_pack(stored_language)
                    if normalised_stored != maybe_stored:
                        chat_data["preferred_language"] = normalised_stored

        normalised = normalize_language_code(language_code)
        if normalised:
            if stored_pack:
                return stored_pack
            if normalised in AVAILABLE_LANGUAGE_CODES and isinstance(chat_data, dict):
                chat_data["preferred_language"] = normalised
            return get_text_pack(normalised)

        if stored_pack:
            return stored_pack

        return get_text_pack(None)

    async def _compose_xp_leaderboard(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        texts: TextPack,
    ) -> Tuple[str, ParseMode | None, InlineKeyboardMarkup | None]:
        leaderboard = self.storage.get_xp_leaderboard(chat_id, self.xp_limit)
        if not leaderboard:
            return (texts.group_no_data, None, None)
        resolved = await self._resolve_leaderboard_names(context, chat_id, leaderboard)
        lines: List[str] = [texts.group_xp_leaderboard_title]
        for index, (display_name, xp) in enumerate(resolved, start=1):
            safe_name = escape(str(display_name))
            lines.append(f"{index}. <b>{safe_name}</b> — <code>{xp}</code>")
        text = "\n".join(lines)
        markup = leaderboard_refresh_keyboard("xp", chat_id, texts)
        return (text, ParseMode.HTML, markup)

    def _compose_cup_leaderboard(
        self,
        chat_id: int,
        texts: TextPack,
    ) -> Tuple[str, ParseMode | None, InlineKeyboardMarkup | None]:
        cups = self.storage.get_cups(chat_id, self.cups_limit)
        if not cups:
            return (texts.group_no_data, None, None)
        lines: List[str] = [texts.group_cup_leaderboard_title]
        for cup in cups:
            title = escape(str(cup.get("title", "")))
            description = escape(str(cup.get("description", "")))
            podium_entries = [escape(str(slot)) for slot in cup.get("podium", []) if slot]
            separator = "، " if texts is PERSIAN_TEXTS else ", "
            podium = separator.join(podium_entries) if podium_entries else "—"
            lines.append(f"<b>{title}</b> — {description}\n🥇 {podium}")
        text = "\n\n".join(lines)
        markup = leaderboard_refresh_keyboard("cups", chat_id, texts)
        return (text, ParseMode.HTML, markup)

    def _resolve_target_from_message(self, message) -> object | None:
        reply = getattr(message, "reply_to_message", None)
        if reply and getattr(reply, "from_user", None):
            return reply.from_user
        return None

    async def _fetch_member(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        raw_identifier: str,
    ) -> object | None:
        candidate = str(raw_identifier).strip()
        if not candidate:
            return None
        try:
            target_id = int(candidate.lstrip("@"))
        except ValueError:
            return None
        try:
            member = await context.bot.get_chat_member(chat_id, target_id)
        except Exception:
            return None
        return getattr(member, "user", None)

