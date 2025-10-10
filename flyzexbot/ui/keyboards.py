from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from ..localization import TextPack, get_default_text_pack


LANGUAGE_CODES: tuple[str, ...] = ("fa", "en")
DEFAULT_LANGUAGE_LABELS: dict[str, str] = {"fa": "فارسی", "en": "English"}


def group_admin_panel_keyboard(
    texts: TextPack | None = None,
    *,
    menu: str = "root",
) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()

    if menu == "ban":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"🚫 {text_pack.group_panel_menu_ban_execute_button}",
                    callback_data="group_panel:action:ban",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_menu_ban_help_button}",
                    callback_data="group_panel:action:ban_help",
                )
            ],
        ]
    elif menu == "mute":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"🔇 {text_pack.group_panel_menu_mute_execute_button}",
                    callback_data="group_panel:action:mute",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_menu_mute_help_button}",
                    callback_data="group_panel:action:mute_help",
                )
            ],
        ]
    elif menu == "xp":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"📋 {text_pack.group_panel_menu_xp_list_button}",
                    callback_data="group_panel:action:xp_members",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"✨ {text_pack.group_panel_menu_xp_add_button}",
                    callback_data="group_panel:action:add_xp",
                ),
                InlineKeyboardButton(
                    text=f"➖ {text_pack.group_panel_menu_xp_remove_button}",
                    callback_data="group_panel:action:remove_xp",
                ),
            ],
        ]
    elif menu == "cups":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"🏆 {text_pack.group_panel_menu_cups_latest_button}",
                    callback_data="group_panel:action:cups_latest",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_menu_cups_howto_button}",
                    callback_data="group_panel:action:cups_help",
                )
            ],
        ]
    elif menu == "admins":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"🛡️ {text_pack.group_panel_menu_admins_list_button}",
                    callback_data="group_panel:action:admins_list",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_menu_admins_howto_button}",
                    callback_data="group_panel:action:admins_help",
                )
            ],
        ]
    elif menu == "settings":
        rows = [
            [
                InlineKeyboardButton(
                    text=f"🌐 {text_pack.group_panel_menu_settings_tools_button}",
                    callback_data="group_panel:action:settings_tools",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_menu_settings_help_button}",
                    callback_data="group_panel:action:settings_help",
                )
            ],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"ℹ️ {text_pack.group_panel_help_button}",
                    callback_data="group_panel:help",
                ),
                InlineKeyboardButton(
                    text=f"🔄 {text_pack.group_panel_refresh_button}",
                    callback_data="group_panel:refresh",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🚫 {text_pack.group_panel_ban_button}",
                    callback_data="group_panel:menu:ban",
                ),
                InlineKeyboardButton(
                    text=f"🔇 {text_pack.group_panel_mute_button}",
                    callback_data="group_panel:menu:mute",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"✨ {text_pack.group_panel_add_xp_button}",
                    callback_data="group_panel:menu:xp",
                ),
                InlineKeyboardButton(
                    text=f"🏆 {text_pack.group_panel_manage_cups_button}",
                    callback_data="group_panel:menu:cups",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🛡️ {text_pack.group_panel_manage_admins_button}",
                    callback_data="group_panel:menu:admins",
                ),
                InlineKeyboardButton(
                    text=f"⚙️ {text_pack.group_panel_settings_button}",
                    callback_data="group_panel:menu:settings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"✖️ {text_pack.group_panel_close_button}",
                    callback_data="group_panel:close",
                )
            ],
        ]

    if menu != "root":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"⬅️ {text_pack.group_panel_menu_back_button}",
                    callback_data="group_panel:menu:root",
                )
            ]
        )

    return InlineKeyboardMarkup(rows)


def glass_dm_welcome_keyboard(
    texts: TextPack | None = None,
    webapp_url: str | None = None,
    *,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    rows = [
        [
            InlineKeyboardButton(
                text=f"🪟 {text_pack.dm_apply_button}",
                callback_data="apply_for_guild",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📨 {text_pack.dm_status_button}",
                callback_data="application_status",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"❌ {text_pack.dm_withdraw_button}",
                callback_data="application_withdraw",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🌐 {text_pack.dm_language_button}",
                callback_data="language_menu",
            )
        ],
    ]
    if webapp_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🧊 {text_pack.dm_open_webapp_button}",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        )
    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🛡️ {text_pack.dm_admin_panel_button}",
                    callback_data="admin_panel",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def admin_panel_keyboard(
    texts: TextPack | None = None,
    webapp_url: str | None = None,
) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"📬 {text_pack.dm_admin_panel_view_applications_button}",
                callback_data="admin_panel:view_applications",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"✅ {text_pack.dm_admin_panel_view_members_button}",
                callback_data="admin_panel:view_members",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🧑‍💼 {text_pack.dm_admin_panel_manage_admins_button}",
                callback_data="admin_panel:manage_admins",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🛠️ {text_pack.dm_admin_panel_manage_questions_button}",
                callback_data="admin_panel:manage_questions",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📊 {text_pack.dm_admin_panel_insights_button}",
                callback_data="admin_panel:insights",
            )
        ],
    ]
    if webapp_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🌐 {text_pack.dm_admin_panel_more_tools_button}",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✨ {text_pack.dm_admin_panel_more_tools_button}",
                    callback_data="admin_panel:more_tools",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"⬅️ {text_pack.dm_admin_panel_back_button}",
                callback_data="admin_panel:back",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def admin_questions_keyboard(
    texts: TextPack | None = None,
    *,
    role_keys: tuple[str, ...] | None = None,
) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    buttons: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=text_pack.dm_admin_questions_role_label,
                callback_data="admin_panel:manage_questions:role_prompt",
            )
        ],
    ]

    followup_template = getattr(
        text_pack,
        "dm_admin_questions_followup_label_template",
        "{role}",
    )
    options = text_pack.dm_application_role_options
    keys = role_keys or tuple(options.keys())
    for key in keys:
        labels = options.get(key, [])
        role_label = labels[0] if labels else key
        buttons.append(
            [
                InlineKeyboardButton(
                    text=followup_template.format(role=role_label),
                    callback_data=f"admin_panel:manage_questions:followup:{key}",
                )
            ]
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text=text_pack.dm_admin_questions_goals_label,
                    callback_data="admin_panel:manage_questions:goals_prompt",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text_pack.dm_admin_questions_availability_label,
                    callback_data="admin_panel:manage_questions:availability_prompt",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text_pack.dm_admin_questions_back_button,
                    callback_data="admin_panel:manage_questions:back",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(buttons)


def admin_management_keyboard(texts: TextPack | None = None) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=f"➕ {text_pack.dm_admin_manage_add_button}",
                    callback_data="admin_panel:manage_admins:add",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"➖ {text_pack.dm_admin_manage_remove_button}",
                    callback_data="admin_panel:manage_admins:remove",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📋 {text_pack.dm_admin_manage_list_button}",
                    callback_data="admin_panel:manage_admins:list",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⬅️ {text_pack.dm_admin_manage_back_button}",
                    callback_data="admin_panel:manage_admins:back",
                )
            ],
        ]
    )


def application_review_keyboard(user_id: int, texts: TextPack | None = None) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text_pack.dm_application_action_buttons["approve"],
                    callback_data=f"application:{user_id}:approve",
                ),
                InlineKeyboardButton(
                    text_pack.dm_application_action_buttons["deny"],
                    callback_data=f"application:{user_id}:deny",
                ),
            ],
            [
                InlineKeyboardButton(
                    text_pack.dm_application_action_buttons["skip"],
                    callback_data="application:skip",
                )
            ],
        ]
    )


def language_options_keyboard(active: str | None, texts: TextPack | None = None) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    rows: list[list[InlineKeyboardButton]] = []
    for code in LANGUAGE_CODES:
        language_names = getattr(text_pack, "language_names", {})
        label = language_names.get(code, DEFAULT_LANGUAGE_LABELS.get(code, code))
        prefix = "✅ " if code == active else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"set_language:{code}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=text_pack.dm_language_close_button,
                callback_data="close_language_menu",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def leaderboard_refresh_keyboard(board_type: str, chat_id: int, texts: TextPack | None = None) -> InlineKeyboardMarkup:
    text_pack = texts or get_default_text_pack()
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=text_pack.group_refresh_button,
                    callback_data=f"leaderboard:{board_type}:{chat_id}",
                )
            ]
        ]
    )
