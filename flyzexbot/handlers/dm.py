from __future__ import annotations

from html import escape
import logging
from typing import Any, Dict, List
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from ..localization import (AVAILABLE_LANGUAGE_CODES, PERSIAN_TEXTS, TextPack,
                            get_text_pack, normalize_language_code)
from ..services.analytics import AnalyticsTracker, NullAnalytics
from ..services.security import RateLimitGuard
from ..services.storage import (
    Application,
    ApplicationHistoryEntry,
    ApplicationResponse,
    Storage,
)
from ..ui.keyboards import (admin_management_keyboard, admin_panel_keyboard,
                            admin_questions_keyboard,
                            application_review_keyboard,
                            glass_dm_welcome_keyboard,
                            language_options_keyboard)

LOGGER = logging.getLogger(__name__)

class DMHandlers:
    def __init__(
        self,
        storage: Storage,
        owner_id: int,
        analytics: AnalyticsTracker | NullAnalytics | None = None,
        rate_limiter: RateLimitGuard | None = None,
    ) -> None:
        self.storage = storage
        self.owner_id = owner_id
        self.analytics = analytics or NullAnalytics()
        self.rate_limiter = rate_limiter or RateLimitGuard(10.0, 5)

    def build_handlers(self) -> list:
        private_filter = filters.ChatType.PRIVATE
        return [
            CommandHandler("start", self.start, filters=private_filter),
            CommandHandler("cancel", self.cancel, filters=private_filter),
            MessageHandler(private_filter & filters.TEXT & ~filters.COMMAND, self.receive_application),
            CallbackQueryHandler(self.handle_apply_callback, pattern="^apply_for_guild$"),
            CallbackQueryHandler(self.show_admin_panel, pattern="^admin_panel$"),
            CallbackQueryHandler(self.handle_admin_panel_action, pattern=r"^admin_panel:"),
            CallbackQueryHandler(self.show_status_callback, pattern="^application_status$"),
            CallbackQueryHandler(self.handle_withdraw_callback, pattern="^application_withdraw$"),
            CallbackQueryHandler(self.show_language_menu, pattern="^language_menu$"),
            CallbackQueryHandler(self.close_language_menu, pattern="^close_language_menu$"),
            CallbackQueryHandler(self.set_language_callback, pattern=r"^set_language:"),
            CallbackQueryHandler(self.handle_application_action, pattern=r"^application:"),
            CommandHandler("pending", self.list_applications),
            CommandHandler("admins", self.list_admins),
            CommandHandler("promote", self.promote_admin),
            CommandHandler("demote", self.demote_admin),
            CommandHandler("status", self.status),
            CommandHandler("withdraw", self.withdraw),
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        user = update.effective_user
        if chat is None:
            return
        language_code = getattr(user, "language_code", None) if user else None
        texts = self._get_texts(context, language_code)
        is_admin = self._is_admin(user.id) if user else False
        await self.analytics.record("dm.start")
        try:
            await chat.send_message(
                text=self._build_welcome_text(texts),
                reply_markup=glass_dm_welcome_keyboard(
                    texts,
                    self._get_webapp_url(context),
                    is_admin=is_admin,
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            LOGGER.error("Failed to send welcome message: %s", exc)

    async def handle_apply_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return

        await query.answer()
        user = query.from_user
        if user is None:
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        await self.analytics.record("dm.apply_requested")
        status_entry = self._get_application_status(user.id)
        if status_entry and getattr(status_entry, "status", "").casefold() == "approved":
            await query.edit_message_text(texts.dm_application_already_member)
            return
        if self.storage.has_application(user.id):
            await query.edit_message_text(texts.dm_application_duplicate)
            return

        active_language = self._get_active_language_code(
            context,
            getattr(user, "language_code", None),
        )
        flow_state = {
            "step": "role",
            "answers": [],
            "language_code": active_language,
        }
        if isinstance(context.user_data, dict):
            context.user_data["is_filling_application"] = True
            context.user_data["application_flow"] = flow_state
        await query.edit_message_text(
            text=texts.dm_application_started,
        )
        chat = query.message.chat if query.message else None
        if chat is not None:
            role_prompt = self._resolve_question_prompt(
                "role_prompt",
                texts,
                active_language,
            )
            await chat.send_message(role_prompt)
        return

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return

        user = query.from_user
        message = query.message
        if user is None or message is None:
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        if not self._is_admin(user.id):
            await query.answer(texts.dm_admin_only, show_alert=True)
            return

        await query.answer()
        await query.edit_message_text(
            text=self._build_admin_panel_text(texts),
            reply_markup=admin_panel_keyboard(
                texts,
                self._get_webapp_url(context),
            ),
            parse_mode=ParseMode.HTML,
        )
        await self.analytics.record("dm.admin_panel_opened")

    async def handle_admin_panel_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return

        data = query.data or ""
        parts = data.split(":", 1)
        if len(parts) != 2:
            await query.answer()
            return

        _, action = parts
        user = query.from_user
        message = query.message
        if user is None or message is None:
            await query.answer()
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        if not self._is_admin(user.id):
            await query.answer(texts.dm_admin_only, show_alert=True)
            return

        chat = message.chat

        if action == "view_applications":
            await query.answer()
            if chat is not None:
                await self._send_pending_applications(chat, texts)
            await self.analytics.record("dm.admin_panel_view_applications")
            return

        if action == "view_members":
            await query.answer()
            if chat is not None:
                members_text = self._render_members_list(
                    self.storage.get_applicants_by_status("approved"),
                    texts,
                )
                await chat.send_message(members_text, parse_mode=ParseMode.HTML)
            await self.analytics.record("dm.admin_panel_view_members")
            return

        if action.startswith("manage_admins"):
            if user.id != self.owner_id:
                await query.answer(texts.dm_not_owner, show_alert=True)
                return

            sub_action = ""
            if ":" in action:
                _, sub_action = action.split(":", 1)

            if sub_action == "":
                await query.answer()
                management_text = self._build_admin_management_text(texts)
                await query.edit_message_text(
                    text=management_text,
                    reply_markup=admin_management_keyboard(texts),
                    parse_mode=ParseMode.HTML,
                )
                await self.analytics.record("dm.admin_panel_manage_admins_opened")
                return

            if sub_action == "add":
                await query.answer()
                if isinstance(context.user_data, dict):
                    context.user_data["pending_admin_action"] = "promote"
                if chat is not None:
                    await chat.send_message(texts.dm_admin_panel_add_admin_prompt)
                await self.analytics.record("dm.admin_panel_manage_admins_add")
                return

            if sub_action == "remove":
                await query.answer()
                if isinstance(context.user_data, dict):
                    context.user_data["pending_admin_action"] = "demote"
                if chat is not None:
                    await chat.send_message(texts.dm_admin_enter_user_id)
                await self.analytics.record("dm.admin_panel_manage_admins_remove")
                return

            if sub_action == "list":
                await query.answer()
                if chat is not None:
                    admins_text = self._render_admins_list(texts)
                    await chat.send_message(admins_text, parse_mode=ParseMode.HTML)
                await self.analytics.record("dm.admin_panel_manage_admins_list")
                return

            if sub_action == "back":
                await query.answer()
                await query.edit_message_text(
                    text=self._build_admin_panel_text(texts),
                    reply_markup=admin_panel_keyboard(
                        texts,
                        self._get_webapp_url(context),
                    ),
                    parse_mode=ParseMode.HTML,
                )
                await self.analytics.record("dm.admin_panel_manage_admins_back")
                return

        if action.startswith("manage_questions"):
            await query.answer()
            sub_action = ""
            if ":" in action:
                _, sub_action = action.split(":", 1)

            active_language = self._get_active_language_code(
                context,
                getattr(user, "language_code", None),
            )
            language_label = self._get_language_label(texts, active_language)

            if sub_action == "" or sub_action == "menu":
                intro = texts.dm_admin_questions_menu_intro.format(
                    reset_keyword=texts.dm_admin_questions_reset_keyword
                )
                menu_text = (
                    f"{texts.dm_admin_questions_menu_title.format(language=language_label)}"
                    f"\n\n{intro}"
                )
                await query.edit_message_text(
                    text=menu_text,
                    reply_markup=admin_questions_keyboard(texts),
                    parse_mode=ParseMode.HTML,
                )
                await self.analytics.record("dm.admin_panel_manage_questions_opened")
                return

            if sub_action == "back":
                await query.edit_message_text(
                    text=self._build_admin_panel_text(texts),
                    reply_markup=admin_panel_keyboard(
                        texts,
                        self._get_webapp_url(context),
                    ),
                    parse_mode=ParseMode.HTML,
                )
                await self.analytics.record("dm.admin_panel_manage_questions_back")
                return

            question_id = sub_action
            if sub_action.startswith("followup:"):
                _, role_key = sub_action.split(":", 1)
                question_id = f"followup_{role_key}"

            label = self._get_question_label(question_id, texts)
            current_prompt = self._resolve_question_prompt(
                question_id,
                texts,
                active_language,
            )
            prompt_text = texts.dm_admin_questions_prompt.format(
                label=label,
                reset_keyword=texts.dm_admin_questions_reset_keyword,
                current=current_prompt or "—",
            )

            if isinstance(context.user_data, dict):
                context.user_data["pending_question_edit"] = {
                    "question_id": question_id,
                    "language_code": active_language,
                    "label": label,
                }

            if chat is not None:
                await chat.send_message(prompt_text)

            await self.analytics.record("dm.admin_panel_manage_questions_prompt")
            return

        if action == "insights":
            await query.answer()
            stats_getter = getattr(self.storage, "get_application_statistics", None)
            if callable(stats_getter) and chat is not None:
                stats = stats_getter()
                insights_text = self._render_admin_insights(stats, texts)
                await chat.send_message(insights_text, parse_mode=ParseMode.HTML)
            await self.analytics.record("dm.admin_panel_insights")
            return

        if action == "more_tools":
            await query.answer()
            if chat is not None:
                webapp_url = self._get_webapp_url(context)
                if webapp_url:
                    await chat.send_message(
                        texts.dm_admin_panel_more_tools_text.format(webapp_url=webapp_url),
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await chat.send_message(texts.dm_admin_panel_more_tools_no_webapp)
            await self.analytics.record("dm.admin_panel_more_tools")
            return

        if action == "back":
            await query.answer()
            await query.edit_message_text(
                text=self._build_welcome_text(texts),
                reply_markup=glass_dm_welcome_keyboard(
                    texts,
                    self._get_webapp_url(context),
                    is_admin=True,
                ),
                parse_mode=ParseMode.HTML,
            )
            await self.analytics.record("dm.admin_panel_back")
            return

        await query.answer()

    async def receive_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        pending_note = context.user_data.get("pending_review_note") if isinstance(context.user_data, dict) else None
        if pending_note:
            await self._process_admin_note_response(update, context)
            return

        pending_question = (
            context.user_data.get("pending_question_edit")
            if isinstance(context.user_data, dict)
            else None
        )
        if pending_question:
            await self._process_question_edit_response(update, context)
            return

        if isinstance(context.user_data, dict):
            pending_action = context.user_data.get("pending_admin_action")
            if pending_action == "promote":
                await self._process_admin_promote_response(update, context)
                return
            if pending_action == "demote":
                await self._process_admin_demote_response(update, context)
                return

        if not context.user_data.get("is_filling_application"):
            return

        user = update.effective_user
        if user is None or update.message is None:
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        status_entry = self._get_application_status(user.id)
        if status_entry and getattr(status_entry, "status", "").casefold() == "approved":
            await update.message.reply_text(texts.dm_application_already_member)
            context.user_data.pop("is_filling_application", None)
            context.user_data.pop("application_flow", None)
            return
        if not await self.rate_limiter.is_allowed(user.id):
            await self.analytics.record("dm.rate_limited")
            await update.message.reply_text(texts.dm_rate_limited)
            return
        answer = update.message.text.strip()
        if not isinstance(context.user_data, dict):
            return

        flow_state = context.user_data.get("application_flow")
        if isinstance(flow_state, dict):
            language_code = flow_state.get("language_code")
            if language_code is None:
                language_code = self._get_active_language_code(
                    context,
                    getattr(user, "language_code", None),
                )
                flow_state["language_code"] = language_code
            completed = await self._handle_application_flow_step(
                update,
                context,
                texts,
                answer,
                flow_state,
                language_code,
            )
            if completed:
                context.user_data.pop("is_filling_application", None)
                context.user_data.pop("application_flow", None)
            return

        try:
            async with self.analytics.track_time("dm.application_store"):
                success = await self.storage.add_application(
                    user_id=user.id,
                    full_name=user.full_name or user.username or str(user.id),
                    username=getattr(user, "username", None),
                    answer=answer,
                    language_code=context.user_data.get("preferred_language"),
                )
        except Exception as exc:
            LOGGER.error("Failed to persist application for %s: %s", user.id, exc)
            await self.analytics.record("dm.application_error")
            await update.message.reply_text(texts.error_generic)
            context.user_data.pop("is_filling_application", None)
            return
        if not success:
            LOGGER.warning("Duplicate application prevented for user %s", user.id)
            await update.message.reply_text(texts.dm_application_duplicate)
            context.user_data.pop("is_filling_application", None)
            return

        await update.message.reply_text(texts.dm_application_received)
        await self.analytics.record("dm.application_submitted")
        review_chat_id = context.bot_data.get("review_chat_id")
        if review_chat_id and context.application:
            context.application.create_task(
                context.bot.send_message(
                    chat_id=review_chat_id,
                    text=self._render_application_text(user.id),
                    parse_mode=ParseMode.HTML,
                    reply_markup=application_review_keyboard(user.id, PERSIAN_TEXTS),
                )
            )
        context.user_data.pop("is_filling_application", None)
        return

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.pop("is_filling_application", None)
        context.user_data.pop("pending_admin_action", None)
        context.user_data.pop("application_flow", None)
        context.user_data.pop("pending_question_edit", None)
        language_code = getattr(update.effective_user, "language_code", None)
        texts = self._get_texts(context, language_code)
        if update.message:
            await update.message.reply_text(texts.dm_cancelled)
        await self.analytics.record("dm.cancelled")

    async def list_applications(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        if not self._is_admin(user.id):
            await chat.send_message(texts.dm_admin_only)
            return
        await self._send_pending_applications(chat, texts)

    async def handle_application_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()

        user = query.from_user
        language_code = getattr(user, "language_code", None) if user else None
        admin_texts = self._get_texts(context, language_code)
        if user is None:
            return
        if not self._is_admin(user.id):
            await query.edit_message_text(admin_texts.dm_admin_only)
            return

        data = query.data
        if data == "application:skip":
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([]))
            await self.analytics.record("dm.admin_skip_application")
            return

        _, user_id_str, action = data.split(":")
        target_id = int(user_id_str)
        application = await self.storage.pop_application(target_id)
        if not application:
            await query.edit_message_text(admin_texts.dm_no_pending)
            return

        applicant_texts = get_text_pack(application.language_code)
        message = query.message
        if message is None:
            return

        application_text = self._format_application_entry(application, admin_texts)
        prompt_template = admin_texts.dm_application_note_prompts.get(action)
        if not prompt_template:
            LOGGER.error("Missing note prompt for action %s", action)
            prompt_template = ""

        prompt_text = prompt_template.format(
            full_name=escape(str(application.full_name)),
            user_id=target_id,
        )
        skip_hint = admin_texts.dm_application_note_skip_hint

        context.user_data["pending_review_note"] = {
            "action": action,
            "target_id": target_id,
            "applicant_texts": applicant_texts,
            "admin_texts": admin_texts,
            "application_text": application_text,
            "chat_id": message.chat_id,
            "message_id": message.message_id,
            "full_name": application.full_name,
            "language_code": application.language_code,
        }

        await message.edit_text(
            text=f"{application_text}\n\n{prompt_text}\n{skip_hint}",
            parse_mode=ParseMode.HTML,
        )

    async def _process_admin_note_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        pending_note = context.user_data.get("pending_review_note")
        if not isinstance(pending_note, dict):
            texts = self._get_texts(context, getattr(user, "language_code", None))
            await message.reply_text(texts.dm_application_note_no_active)
            return

        admin_texts: TextPack = pending_note["admin_texts"]
        applicant_texts: TextPack = pending_note["applicant_texts"]
        action: str = pending_note["action"]
        target_id: int = pending_note["target_id"]
        chat_id: int = pending_note["chat_id"]
        message_id: int = pending_note["message_id"]
        application_text: str = pending_note["application_text"]

        note_raw = (message.text or "").strip()
        skip_keyword = admin_texts.dm_application_note_skip_keyword.casefold()
        is_skip = not note_raw or note_raw.casefold() == skip_keyword
        note_to_store = None if is_skip else note_raw

        try:
            status = "approved" if action == "approve" else "denied"
            await self.storage.mark_application_status(
                target_id,
                status,
                note=note_to_store,
                language_code=pending_note.get("language_code"),
            )

            applicant_message = (
                applicant_texts.dm_application_approved_user
                if action == "approve"
                else applicant_texts.dm_application_denied_user
            )
            if note_to_store:
                applicant_message = (
                    f"{applicant_message}\n\n📝 {applicant_texts.dm_application_note_label}: {note_to_store}"
                )
            await self._notify_user(context, target_id, applicant_message)

            confirmation_template = admin_texts.dm_application_note_confirmations.get(action, "")
            confirmation_text = confirmation_template.format(
                full_name=escape(str(pending_note.get("full_name", target_id))),
                user_id=target_id,
            )
            final_text = f"{application_text}\n\n{confirmation_text}"
            if note_to_store:
                final_text = (
                    f"{final_text}\n📝 {admin_texts.dm_application_note_label}: {escape(note_to_store)}"
                )

            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=final_text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as exc:  # pragma: no cover - network failures are logged
                LOGGER.error("Failed to edit admin message for %s: %s", target_id, exc)

            analytics_event = (
                "dm.admin_application_approved"
                if action == "approve"
                else "dm.admin_application_denied"
            )
            await self.analytics.record(analytics_event)
        finally:
            context.user_data.pop("pending_review_note", None)

    async def _process_question_edit_response(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        message = update.message
        user = update.effective_user
        if message is None or user is None:
            return

        if not isinstance(context.user_data, dict):
            return

        pending = context.user_data.get("pending_question_edit")
        texts = self._get_texts(context, getattr(user, "language_code", None))
        if not isinstance(pending, dict):
            await message.reply_text(texts.dm_admin_questions_cancelled)
            context.user_data.pop("pending_question_edit", None)
            return

        question_id = pending.get("question_id")
        language_code = pending.get("language_code")
        label = pending.get("label") or self._get_question_label(
            str(question_id),
            texts,
        )

        payload = (message.text or "").strip()
        if not question_id or not payload:
            await message.reply_text(texts.dm_admin_questions_cancelled)
            context.user_data.pop("pending_question_edit", None)
            return

        reset_keyword = texts.dm_admin_questions_reset_keyword.casefold()
        try:
            if payload.casefold() == reset_keyword:
                await self.storage.set_application_question(
                    question_id,
                    None,
                    language_code=language_code,
                )
                await message.reply_text(
                    texts.dm_admin_questions_reset_success.format(label=label)
                )
            else:
                await self.storage.set_application_question(
                    question_id,
                    payload,
                    language_code=language_code,
                )
                await message.reply_text(
                    texts.dm_admin_questions_success.format(label=label)
                )
            await self.analytics.record("dm.admin_panel_manage_questions_saved")
        finally:
            context.user_data.pop("pending_question_edit", None)

    async def _process_admin_promote_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None:
            return

        if user.id != self.owner_id:
            context.user_data.pop("pending_admin_action", None)
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        payload = (message.text or "").strip()
        try:
            target_user_id = int(payload)
        except (TypeError, ValueError):
            await message.reply_text(texts.dm_admin_invalid_user_id)
            return

        added = await self.storage.add_admin(target_user_id)
        if added:
            await chat.send_message(texts.dm_admin_added.format(user_id=target_user_id))
        else:
            await chat.send_message(texts.dm_already_admin.format(user_id=target_user_id))

        context.user_data.pop("pending_admin_action", None)
        await self.analytics.record("dm.admin_panel_promote_completed")


    async def _process_admin_demote_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None:
            return

        if user.id != self.owner_id:
            context.user_data.pop("pending_admin_action", None)
            return

        texts = self._get_texts(context, getattr(user, "language_code", None))
        payload = (message.text or "").strip()
        try:
            target_user_id = int(payload)
        except (TypeError, ValueError):
            await message.reply_text(texts.dm_admin_invalid_user_id)
            return

        removed = await self.storage.remove_admin(target_user_id)
        if removed:
            await chat.send_message(texts.dm_admin_removed.format(user_id=target_user_id))
        else:
            await chat.send_message(texts.dm_not_admin.format(user_id=target_user_id))

        context.user_data.pop("pending_admin_action", None)
        await self.analytics.record("dm.admin_panel_demote_completed")


    async def _notify_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str) -> None:
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as exc:
            LOGGER.error("Failed to notify user %s: %s", user_id, exc)

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat is None:
            return
        language_code = getattr(update.effective_user, "language_code", None)
        texts = self._get_texts(context, language_code)
        admins_text = self._render_admins_list(texts)
        if admins_text == texts.dm_admin_manage_list_empty:
            await chat.send_message(texts.dm_no_admins)
            return
        await chat.send_message(admins_text, parse_mode=ParseMode.HTML)

    async def promote_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._check_owner(update):
            return
        chat = update.effective_chat
        if chat is None:
            return
        language_code = getattr(update.effective_user, "language_code", None)
        texts = self._get_texts(context, language_code)
        if not context.args:
            await chat.send_message(texts.dm_admin_enter_user_id)
            return
        try:
            user_id = int(context.args[0])
        except ValueError:
            await chat.send_message(texts.dm_admin_invalid_user_id)
            return
        added = await self.storage.add_admin(user_id)
        if added:
            await chat.send_message(texts.dm_admin_added.format(user_id=user_id))
        else:
            await chat.send_message(texts.dm_already_admin.format(user_id=user_id))

    async def demote_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._check_owner(update):
            return
        chat = update.effective_chat
        if chat is None:
            return
        language_code = getattr(update.effective_user, "language_code", None)
        texts = self._get_texts(context, language_code)
        if not context.args:
            await chat.send_message(texts.dm_admin_enter_user_id)
            return
        try:
            user_id = int(context.args[0])
        except ValueError:
            await chat.send_message(texts.dm_admin_invalid_user_id)
            return
        removed = await self.storage.remove_admin(user_id)
        if removed:
            await chat.send_message(texts.dm_admin_removed.format(user_id=user_id))
        else:
            await chat.send_message(texts.dm_not_admin.format(user_id=user_id))

    async def _check_owner(self, update: Update) -> bool:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return False
        if user.id != self.owner_id:
            texts = get_text_pack(getattr(user, "language_code", None))
            await chat.send_message(texts.dm_not_owner)
            return False
        return True

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        text = self._render_status_text(self.storage.get_application_status(user.id), texts)
        await chat.send_message(text, parse_mode=ParseMode.HTML)
        await self.analytics.record("dm.status_requested")

    async def show_status_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        user = query.from_user
        if user is None:
            return
        message = query.message
        if message is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        text = self._render_status_text(self.storage.get_application_status(user.id), texts)
        await message.chat.send_message(text, parse_mode=ParseMode.HTML)
        await self.analytics.record("dm.status_requested")

    async def withdraw(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        success = await self.storage.withdraw_application(user.id)
        context.user_data.pop("is_filling_application", None)
        context.user_data.pop("application_flow", None)
        if success:
            await chat.send_message(texts.dm_withdraw_success)
            await self.analytics.record("dm.withdraw_completed")
        else:
            await chat.send_message(texts.dm_withdraw_not_found)
            await self.analytics.record("dm.withdraw_missing")

    async def handle_withdraw_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        user = query.from_user
        if user is None:
            return
        message = query.message
        if message is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None))
        success = await self.storage.withdraw_application(user.id)
        context.user_data.pop("is_filling_application", None)
        context.user_data.pop("application_flow", None)
        if success:
            await message.chat.send_message(texts.dm_withdraw_success)
            await self.analytics.record("dm.withdraw_completed")
        else:
            await message.chat.send_message(texts.dm_withdraw_not_found)
            await self.analytics.record("dm.withdraw_missing")

    async def show_language_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        user = query.from_user
        message = query.message
        if message is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None) if user else None)
        active = context.user_data.get("preferred_language") if isinstance(context.user_data, dict) else None
        await message.edit_text(
            text=texts.dm_language_menu_title,
            reply_markup=language_options_keyboard(active if isinstance(active, str) else None, texts),
        )
        await self.analytics.record("dm.language_menu_opened")

    async def close_language_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        message = query.message
        user = query.from_user
        if message is None:
            return
        texts = self._get_texts(context, getattr(user, "language_code", None) if user else None)
        is_admin = self._is_admin(user.id) if user else False
        await message.edit_text(
            text=self._build_welcome_text(texts),
            reply_markup=glass_dm_welcome_keyboard(
                texts,
                self._get_webapp_url(context),
                is_admin=is_admin,
            ),
            parse_mode=ParseMode.HTML,
        )
        await self.analytics.record("dm.language_menu_closed")

    async def set_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        data = query.data or ""
        parts = data.split(":", 1)
        if len(parts) != 2:
            await query.answer()
            return
        _, code = parts
        normalised = normalize_language_code(code) or code
        if isinstance(context.user_data, dict):
            context.user_data["preferred_language"] = normalised
        user = query.from_user
        new_texts = get_text_pack(normalised)
        await self.analytics.record("dm.language_updated")
        await query.answer(new_texts.dm_language_updated, show_alert=True)
        message = query.message
        if message is None:
            return
        is_admin = self._is_admin(user.id) if user else False
        await message.edit_text(
            text=self._build_welcome_text(new_texts),
            reply_markup=glass_dm_welcome_keyboard(
                new_texts,
                self._get_webapp_url(context),
                is_admin=is_admin,
            ),
            parse_mode=ParseMode.HTML,
        )

    def _build_welcome_text(self, texts: TextPack) -> str:
        return f"{texts.dm_welcome}\n\n{texts.glass_panel_caption}"

    def _build_admin_panel_text(self, texts: TextPack) -> str:
        return f"{texts.dm_admin_panel_intro}\n\n{texts.glass_panel_caption}"

    def _build_admin_management_text(self, texts: TextPack) -> str:
        admins_list = self._render_admins_list(texts)
        return "\n\n".join(
            [texts.dm_admin_manage_title, texts.dm_admin_manage_intro, admins_list]
        )

    def _render_admins_list(self, texts: TextPack) -> str:
        details_getter = getattr(self.storage, "get_admin_details", None)
        details: List[Dict[str, Any]] | None = None
        if callable(details_getter):
            details = details_getter()
        else:
            list_getter = getattr(self.storage, "list_admins", None)
            if callable(list_getter):
                details = [{"user_id": admin_id} for admin_id in list_getter()]

        if not details:
            return texts.dm_admin_manage_list_empty

        lines: List[str] = [texts.dm_admin_manage_list_header]
        for entry in details:
            user_id = entry.get("user_id")
            if user_id is None:
                continue

            parts: List[str] = []
            full_name = entry.get("full_name")
            if full_name:
                parts.append(escape(str(full_name)))

            username = entry.get("username")
            if username:
                normalised = str(username).lstrip("@")
                if normalised:
                    parts.append(f"@{escape(normalised)}")

            if not parts:
                parts.append(texts.dm_admin_manage_list_unknown)

            display = " / ".join(parts)
            safe_user_id = escape(str(user_id))
            lines.append(
                texts.dm_admin_manage_list_entry.format(
                    display=display,
                    user_id=safe_user_id,
                )
            )

        return "\n".join(lines)

    def _render_members_list(
        self,
        entries: list[tuple[int, ApplicationHistoryEntry]],
        texts: TextPack,
    ) -> str:
        if not entries:
            return texts.dm_admin_panel_members_empty

        lines = []
        for user_id, history in entries[:10]:
            updated_at = escape(getattr(history, "updated_at", ""))
            lines.append(f"• <code>{user_id}</code> – {updated_at}")
        members_block = "\n".join(lines)
        return texts.dm_admin_panel_members_header.format(
            count=len(entries),
            members=members_block,
        )

    async def _send_pending_applications(self, chat, texts: TextPack) -> bool:
        pending = self.storage.get_pending_applications()
        if not pending:
            await chat.send_message(texts.dm_no_pending)
            return False

        await self.analytics.record("dm.admin_pending_list")

        for application in pending[:5]:
            await chat.send_message(
                text=self._format_application_entry(application, texts),
                parse_mode=ParseMode.HTML,
                reply_markup=application_review_keyboard(application.user_id, texts),
            )
        return True

    def _is_admin(self, user_id: int) -> bool:
        checker = getattr(self.storage, "is_admin", None)
        if callable(checker):
            return bool(checker(user_id))
        return False

    def _get_application_status(self, user_id: int) -> ApplicationHistoryEntry | None:
        getter = getattr(self.storage, "get_application_status", None)
        if callable(getter):
            return getter(user_id)
        return None

    def _get_webapp_url(self, context: ContextTypes.DEFAULT_TYPE) -> str | None:
        bot_data = getattr(context, "bot_data", None)
        if isinstance(bot_data, dict):
            url = bot_data.get("webapp_url")
            if isinstance(url, str) and url:
                return url
        return None

    def _render_application_text(self, user_id: int, texts: TextPack | None = None) -> str:
        application = self.storage.get_application(user_id)
        text_pack = texts or PERSIAN_TEXTS
        if not application:
            return text_pack.dm_no_pending
        return self._format_application_entry(application, text_pack)

    def _format_application_entry(self, application: Application, texts: TextPack) -> str:
        full_name = escape(str(application.full_name))
        username = application.username
        if username:
            username = username.lstrip("@")
            username_display = f"@{username}" if username else "—"
        else:
            username_display = "—"
        username_escaped = escape(username_display)
        answers_block = self._format_application_answers(application, texts)
        created_at = escape(str(application.created_at))
        return texts.dm_application_item.format(
            full_name=full_name,
            username=username_escaped,
            user_id=application.user_id,
            answers=answers_block,
            created_at=created_at,
        )

    def _render_status_text(self, status: ApplicationHistoryEntry | None, texts: TextPack | None = None) -> str:
        text_pack = texts or PERSIAN_TEXTS
        if not status:
            return text_pack.dm_status_none

        status_map = {
            "pending": text_pack.dm_status_pending,
            "approved": text_pack.dm_status_approved,
            "denied": text_pack.dm_status_denied,
            "withdrawn": text_pack.dm_status_withdrawn,
        }

        status_label = status_map.get(status.status)
        if not status_label:
            status_label = text_pack.dm_status_unknown.format(status=escape(status.status))

        updated_at = escape(status.updated_at)
        last_updated_label = text_pack.dm_status_last_updated_label

        if status.note:
            note = escape(status.note)
            return text_pack.dm_status_template_with_note.format(
                status=status_label,
                updated_at=updated_at,
                note=note,
                last_updated_label=last_updated_label,
            )

        return text_pack.dm_status_template.format(
            status=status_label,
            updated_at=updated_at,
            last_updated_label=last_updated_label,
        )

    def _get_texts(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        language_code: str | None = None,
    ) -> TextPack:
        user_data = getattr(context, "user_data", None)
        stored_language: str | None = None
        stored_pack: TextPack | None = None
        if isinstance(user_data, dict):
            maybe_stored = user_data.get("preferred_language")
            if isinstance(maybe_stored, str):
                normalised_stored = normalize_language_code(maybe_stored) or maybe_stored
                if normalised_stored in AVAILABLE_LANGUAGE_CODES:
                    stored_language = normalised_stored
                    stored_pack = get_text_pack(stored_language)
                    if normalised_stored != maybe_stored:
                        user_data["preferred_language"] = normalised_stored

        normalised = normalize_language_code(language_code)
        if normalised:
            if stored_pack:
                return stored_pack
            if normalised in AVAILABLE_LANGUAGE_CODES and isinstance(user_data, dict):
                user_data["preferred_language"] = normalised
            return get_text_pack(normalised)

        if stored_pack:
            return stored_pack

        return get_text_pack(None)

    def _get_active_language_code(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        language_code: str | None = None,
    ) -> str | None:
        stored: str | None = None
        if isinstance(context.user_data, dict):
            maybe_stored = context.user_data.get("preferred_language")
            if isinstance(maybe_stored, str):
                stored = normalize_language_code(maybe_stored) or maybe_stored

        requested = normalize_language_code(language_code) if language_code else None
        return stored or requested

    def _get_language_label(self, texts: TextPack, language_code: str | None) -> str:
        language_names = getattr(texts, "language_names", {})
        if language_code and language_code in language_names:
            return language_names[language_code]
        if language_code:
            return language_code
        if language_names:
            return next(iter(language_names.values()))
        return "—"

    def _get_question_overrides(self, language_code: str | None) -> Dict[str, str]:
        getter = getattr(self.storage, "get_application_questions", None)
        if not callable(getter):
            return {}
        try:
            overrides = getter(language_code)
        except TypeError:
            overrides = getter()  # type: ignore[misc]
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to load question overrides")
            return {}
        if not isinstance(overrides, dict):
            return {}
        return {
            str(question_id): str(prompt)
            for question_id, prompt in overrides.items()
            if isinstance(question_id, str) and isinstance(prompt, str)
        }

    def _resolve_question_prompt(
        self,
        question_id: str,
        texts: TextPack,
        language_code: str | None,
    ) -> str:
        overrides = self._get_question_overrides(language_code)
        prompt = overrides.get(question_id)
        if prompt:
            return prompt

        if question_id == "role_prompt":
            return texts.dm_application_role_prompt
        if question_id == "goals_prompt":
            return texts.dm_application_goals_prompt
        if question_id == "availability_prompt":
            return texts.dm_application_availability_prompt
        if question_id.startswith("followup_"):
            role_key = question_id.split("_", 1)[1]
            return texts.dm_application_followup_prompts.get(role_key, "")
        return ""

    def _get_question_label(self, question_id: str, texts: TextPack) -> str:
        if question_id == "role_prompt":
            return texts.dm_admin_questions_role_label
        if question_id == "goals_prompt":
            return texts.dm_admin_questions_goals_label
        if question_id == "availability_prompt":
            return texts.dm_admin_questions_availability_label
        if question_id.startswith("followup_"):
            role_key = question_id.split("_", 1)[1]
            template = getattr(
                texts,
                "dm_admin_questions_followup_label_template",
                "{role}",
            )
            options = texts.dm_application_role_options.get(role_key, [])
            role_label = options[0] if options else role_key
            return template.format(role=role_label)
        return question_id

    async def _handle_application_flow_step(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        texts: TextPack,
        answer: str,
        flow_state: dict,
        language_code: str | None,
    ) -> bool:
        message = update.message
        if message is None:
            return False

        step = flow_state.get("step")
        responses = flow_state.setdefault("answers", [])

        if step == "role":
            match = self._match_role(answer, texts)
            if not match:
                await message.reply_text(
                    texts.dm_application_invalid_choice.format(
                        options=", ".join(self._role_labels(texts))
                    )
                )
                return False

            role_key, provided_answer = match
            role_prompt = self._resolve_question_prompt(
                "role_prompt",
                texts,
                language_code,
            )
            responses.append(
                {
                    "question_id": "role",
                    "question": role_prompt,
                    "answer": provided_answer,
                }
            )
            flow_state["role_key"] = role_key
            prompt = self._resolve_question_prompt(
                f"followup_{role_key}",
                texts,
                language_code,
            )
            if prompt:
                flow_state["step"] = "followup"
                await message.reply_text(prompt)
            else:
                flow_state["step"] = "goals"
                goals_prompt = self._resolve_question_prompt(
                    "goals_prompt",
                    texts,
                    language_code,
                )
                await message.reply_text(goals_prompt)
            return False

        if step == "followup":
            role_key = flow_state.get("role_key")
            question = self._resolve_question_prompt(
                f"followup_{role_key}",
                texts,
                language_code,
            )
            if question:
                responses.append(
                    {
                        "question_id": f"followup_{role_key}",
                        "question": question,
                        "answer": answer,
                    }
                )
            flow_state["step"] = "goals"
            goals_prompt = self._resolve_question_prompt(
                "goals_prompt",
                texts,
                language_code,
            )
            await message.reply_text(goals_prompt)
            return False

        if step == "goals":
            goals_prompt = self._resolve_question_prompt(
                "goals_prompt",
                texts,
                language_code,
            )
            responses.append(
                {
                    "question_id": "goals",
                    "question": goals_prompt,
                    "answer": answer,
                }
            )

            flow_state["step"] = "availability"
            availability_prompt = self._resolve_question_prompt(
                "availability_prompt",
                texts,
                language_code,
            )
            await message.reply_text(availability_prompt)
            return False

        if step == "availability":
            availability_prompt = self._resolve_question_prompt(
                "availability_prompt",
                texts,
                language_code,
            )
            responses.append(
                {
                    "question_id": "availability",
                    "question": availability_prompt,
                    "answer": answer,
                }
            )

            application_responses = [
                ApplicationResponse(
                    question_id=item["question_id"],
                    question=item["question"],
                    answer=item["answer"],
                )
                for item in responses
            ]
            summary_text = self._format_application_summary(application_responses, texts)
            aggregated_answer = self._collapse_responses(application_responses)

            user = update.effective_user
            if user is None:
                return False

            try:
                async with self.analytics.track_time("dm.application_store"):
                    success = await self.storage.add_application(
                        user_id=user.id,
                        full_name=user.full_name or user.username or str(user.id),
                        username=getattr(user, "username", None),
                        answer=aggregated_answer,
                        language_code=context.user_data.get("preferred_language"),
                        responses=application_responses,
                    )
            except Exception as exc:
                LOGGER.error("Failed to persist application for %s: %s", user.id, exc)
                await self.analytics.record("dm.application_error")
                await message.reply_text(texts.error_generic)
                return True

            if not success:
                LOGGER.warning("Duplicate application prevented for user %s", user.id)
                await message.reply_text(texts.dm_application_duplicate)
                return True

            await message.reply_text(summary_text, parse_mode=ParseMode.HTML)
            await message.reply_text(texts.dm_application_received)
            await self.analytics.record("dm.application_submitted")

            review_chat_id = context.bot_data.get("review_chat_id")
            if review_chat_id and context.application:
                context.application.create_task(
                    context.bot.send_message(
                        chat_id=review_chat_id,
                        text=self._render_application_text(user.id),
                        parse_mode=ParseMode.HTML,
                        reply_markup=application_review_keyboard(user.id, PERSIAN_TEXTS),
                    )
                )
            return True

        await message.reply_text(texts.error_generic)
        return True

    def _role_labels(self, texts: TextPack) -> List[str]:
        labels: List[str] = []
        for synonyms in texts.dm_application_role_options.values():
            if synonyms:
                labels.append(synonyms[0])
        return labels

    def _match_role(self, answer: str, texts: TextPack) -> tuple[str, str] | None:
        normalized = answer.casefold()
        for role, synonyms in texts.dm_application_role_options.items():
            for synonym in synonyms:
                if normalized == synonym.casefold():
                    return role, synonym
        return None

    def _format_application_answers(self, application: Application, texts: TextPack) -> str:
        if application.responses:
            lines = [
                texts.dm_application_summary_item.format(
                    question=escape(response.question),
                    answer=escape(response.answer) if response.answer else "—",
                )
                for response in application.responses
            ]
            return "\n".join(lines)

        raw_answer = application.answer if application.answer else "—"
        return escape(str(raw_answer))

    def _format_application_summary(
        self, responses: List[ApplicationResponse], texts: TextPack
    ) -> str:
        lines = [texts.dm_application_summary_title]
        for response in responses:
            lines.append(
                texts.dm_application_summary_item.format(
                    question=escape(response.question),
                    answer=escape(response.answer) if response.answer else "—",
                )
            )
        return "\n".join(lines)

    def _collapse_responses(self, responses: List[ApplicationResponse]) -> str:
        return "\n".join(
            f"{response.question.strip()} {response.answer.strip()}".strip()
            for response in responses
        )

    def _render_admin_insights(self, stats: Dict[str, Any], texts: TextPack) -> str:
        pending = int(stats.get("pending", 0))
        status_counts = stats.get("status_counts", {}) or {}
        approved = int(status_counts.get("approved", 0))
        denied = int(status_counts.get("denied", 0))
        withdrawn = int(status_counts.get("withdrawn", 0))
        total = int(stats.get("total", 0))
        average_length = float(stats.get("average_pending_answer_length", 0.0))

        counts_block = texts.dm_admin_panel_insights_counts.format(
            pending=pending,
            approved=approved,
            denied=denied,
            withdrawn=withdrawn,
            total=total,
            average_length=average_length,
        )

        languages = stats.get("languages", {}) or {}
        if languages:
            language_lines = [
                f"• {escape(str(code))}: {count}"
                for code, count in sorted(languages.items(), key=lambda item: (-int(item[1]), str(item[0])))
            ]
            languages_block = texts.dm_admin_panel_insights_languages.format(
                languages="\n".join(language_lines)
            )
        else:
            languages_block = texts.dm_admin_panel_insights_languages_empty

        recent_updates = stats.get("recent_updates", []) or []
        if recent_updates:
            recent_lines = []
            for entry in recent_updates:
                user_id = escape(str(entry.get("user_id", "—")))
                status = escape(str(entry.get("status", "")))
                updated_at = escape(str(entry.get("updated_at", "")))
                recent_lines.append(f"• <code>{user_id}</code> – {status} ({updated_at})")
            recent_block = texts.dm_admin_panel_insights_recent.format(
                items="\n".join(recent_lines)
            )
        else:
            recent_block = texts.dm_admin_panel_insights_recent_empty

        return "\n".join(
            [
                texts.dm_admin_panel_insights_title,
                counts_block,
                languages_block,
                recent_block,
            ]
        )

