from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from flyzexbot.handlers.group import GroupHandlers
from flyzexbot.localization import PERSIAN_TEXTS
from flyzexbot.services.xp import calculate_level_progress


class DummyChat:
    def __init__(self, chat_id: int = 123) -> None:
        self.id = chat_id
        self.messages: list[str] = []

    async def send_message(self, text: str, **_: object) -> None:  # noqa: ANN003 - kwargs unused
        self.messages.append(text)


class DummyMessage:
    def __init__(self, text: str = "hello") -> None:
        self.text = text
        self.replies: list[str] = []
        self.kwargs: list[dict[str, object]] = []

    async def reply_text(self, text: str, **kwargs: object) -> None:  # noqa: ANN003 - kwargs unused
        self.replies.append(text)
        self.kwargs.append(dict(kwargs))


class DummyUser:
    def __init__(self, user_id: int = 456, language_code: str = "fa") -> None:
        self.id = user_id
        self.language_code = language_code
        self.full_name = "Test User"
        self.username = "test_user"


class DummyContext:
    def __init__(self, args: list[str]) -> None:
        self.args = args
        self.chat_data: dict[str, object] = {}
        self.user_data: dict[str, object] = {}
        self.bot = SimpleNamespace(
            send_message=AsyncMock(),
            get_chat_member=AsyncMock(),
        )


def test_add_cup_accepts_single_argument_string() -> None:
    storage = SimpleNamespace(add_cup=AsyncMock())
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=100,
        cups_limit=10,
    )
    handler._is_admin = AsyncMock(return_value=True)  # type: ignore[method-assign]

    chat = DummyChat()
    user = DummyUser()
    update = SimpleNamespace(effective_chat=chat, effective_user=user)
    context = DummyContext(["Title|Description|A,B,C"])

    asyncio.run(handler.add_cup(update, context))

    storage.add_cup.assert_awaited_once_with(chat.id, "Title", "Description", ["A", "B", "C"])
    assert PERSIAN_TEXTS.group_add_cup_usage not in chat.messages


def test_track_activity_handles_zero_reward() -> None:
    storage = SimpleNamespace(add_xp=AsyncMock(return_value=0))
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=0,
        xp_message_limit=20,
        xp_limit=100,
        cups_limit=10,
    )

    message = DummyMessage()
    chat = SimpleNamespace(id=789)
    user = SimpleNamespace(id=321, full_name="Tester", username="tester")
    update = SimpleNamespace(
        effective_message=message,
        effective_chat=chat,
        effective_user=user,
    )
    context = DummyContext([])

    asyncio.run(handler.track_activity(update, context))

    storage.add_xp.assert_not_awaited()
    assert message.replies == []


def test_command_help_includes_admin_section_for_admins() -> None:
    storage = SimpleNamespace(get_user_xp=Mock(return_value=None), get_group_snapshot=Mock(return_value={}))
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=10,
        cups_limit=5,
    )
    handler._is_admin = AsyncMock(return_value=True)  # type: ignore[method-assign]

    chat = DummyChat()
    user = DummyUser()
    message = DummyMessage()
    update = SimpleNamespace(effective_chat=chat, effective_user=user, effective_message=message)
    context = DummyContext([])

    asyncio.run(handler.command_help(update, context))

    assert message.replies, "Expected help text to be sent"
    text = message.replies[0]
    assert PERSIAN_TEXTS.group_help_admin_title in text
    assert "/panel" in text


def test_command_help_hides_admin_section_for_members() -> None:
    storage = SimpleNamespace(get_user_xp=Mock(return_value=None), get_group_snapshot=Mock(return_value={}))
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=10,
        cups_limit=5,
    )
    handler._is_admin = AsyncMock(return_value=False)  # type: ignore[method-assign]

    chat = DummyChat()
    user = DummyUser()
    message = DummyMessage()
    update = SimpleNamespace(effective_chat=chat, effective_user=user, effective_message=message)
    context = DummyContext([])

    asyncio.run(handler.command_help(update, context))

    assert message.replies, "Expected help text to be sent"
    text = message.replies[0]
    assert PERSIAN_TEXTS.group_help_admin_title not in text
    assert "/panel" not in text


def test_command_myxp_reports_total() -> None:
    storage = SimpleNamespace(
        get_user_xp=Mock(return_value=128),
        get_group_snapshot=Mock(return_value={}),
    )
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=10,
        cups_limit=5,
    )

    chat = DummyChat()
    user = DummyUser()
    message = DummyMessage()
    update = SimpleNamespace(effective_chat=chat, effective_user=user, effective_message=message)
    context = DummyContext([])

    asyncio.run(handler.command_my_xp(update, context))

    assert message.replies, "Expected XP response"
    progress = calculate_level_progress(128)
    expected = PERSIAN_TEXTS.group_myxp_response.format(
        full_name=user.full_name,
        xp=128,
        level=progress.level,
        xp_to_next=progress.xp_to_next,
    )
    assert message.replies[0] == expected


def test_show_panel_escapes_snapshot_content() -> None:
    snapshot = {
        "members_tracked": 3,
        "total_xp": 240,
        "top_member": {"display": "Hero <One>", "xp": 120, "level": 5},
        "cup_count": 2,
        "recent_cup": {"title": "Cup <Alpha>", "created_at": "2024/05/01"},
        "admins_tracked": 2,
        "last_activity": "2024/05/20 · 10:00 UTC",
    }
    storage = SimpleNamespace(get_group_snapshot=Mock(return_value=snapshot))
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=10,
        cups_limit=5,
    )
    handler._is_admin = AsyncMock(return_value=True)  # type: ignore[method-assign]

    chat = SimpleNamespace(id=1, title="Guild <One>")
    user = DummyUser()
    message = DummyMessage()
    update = SimpleNamespace(effective_chat=chat, effective_user=user, effective_message=message)
    context = DummyContext([])

    asyncio.run(handler.show_panel(update, context))

    assert message.replies, "Expected panel message"
    panel_text = message.replies[0]
    assert "Guild &lt;One&gt;" in panel_text
    assert "Hero &lt;One&gt;" in panel_text


def test_compose_group_panel_menu_includes_section_text() -> None:
    storage = SimpleNamespace(get_group_snapshot=Mock(return_value={}))
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=10,
        cups_limit=5,
    )

    chat = SimpleNamespace(id=1, title="Guild")
    text, markup = handler._compose_group_panel(chat, PERSIAN_TEXTS, menu="xp")

    assert PERSIAN_TEXTS.group_panel_menu_xp_title in text
    assert markup.inline_keyboard[0][0].callback_data == "group_panel:action:xp_members"


def test_keyword_xp_triggers_dm_and_summary() -> None:
    storage = SimpleNamespace(
        add_xp=AsyncMock(return_value=12),
        get_user_xp=Mock(return_value=12),
        get_xp_leaderboard=Mock(return_value=[("456", 30), ("789", 20)]),
        get_user_xp_rank=Mock(return_value=(1, 5)),
        get_cups=Mock(return_value=[]),
    )
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=5,
        cups_limit=5,
    )

    message = DummyMessage("XP")
    chat = DummyChat()
    user = DummyUser()
    update = SimpleNamespace(effective_message=message, effective_chat=chat, effective_user=user)
    context = DummyContext([])
    context.bot.get_chat_member.return_value = SimpleNamespace(
        user=SimpleNamespace(full_name="Leader"),
    )

    asyncio.run(handler.track_activity(update, context))

    assert context.bot.send_message.await_count == 1
    assert message.replies, "Expected summary reply"
    progress = calculate_level_progress(12)
    expected = PERSIAN_TEXTS.group_personal_panel_dm_prompt.format(
        xp=12,
        level=progress.level,
        rank="#1",
        trophies=0,
    )
    assert expected in message.replies[0]


def test_keyword_invalid_shows_fallback() -> None:
    storage = SimpleNamespace(
        add_xp=AsyncMock(return_value=10),
        get_user_xp=Mock(return_value=10),
        get_xp_leaderboard=Mock(return_value=[]),
        get_user_xp_rank=Mock(return_value=(None, 0)),
        get_cups=Mock(return_value=[]),
    )
    handler = GroupHandlers(
        storage=storage,
        xp_per_character=1,
        xp_message_limit=20,
        xp_limit=5,
        cups_limit=5,
    )

    message = DummyMessage("XP stats")
    chat = DummyChat()
    user = DummyUser()
    update = SimpleNamespace(effective_message=message, effective_chat=chat, effective_user=user)
    context = DummyContext([])

    asyncio.run(handler.track_activity(update, context))

    assert message.replies == [PERSIAN_TEXTS.group_keyword_fallback]
    assert context.bot.send_message.await_count == 0
