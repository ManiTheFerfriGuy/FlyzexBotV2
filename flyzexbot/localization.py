from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TextPack:
    dm_welcome: str
    dm_apply_button: str
    dm_open_webapp_button: str
    dm_admin_panel_button: str
    dm_status_button: str
    dm_withdraw_button: str
    dm_application_started: str
    dm_application_question: str
    dm_application_received: str
    dm_application_duplicate: str
    dm_application_already_member: str
    dm_application_role_prompt: str
    dm_application_role_options: Dict[str, List[str]]
    dm_application_followup_prompts: Dict[str, str]
    dm_application_goals_prompt: str
    dm_application_availability_prompt: str
    dm_application_summary_title: str
    dm_application_summary_item: str
    dm_application_invalid_choice: str
    dm_admin_only: str
    dm_no_pending: str
    dm_application_item: str
    dm_application_action_buttons: Dict[str, str]
    dm_application_approved_user: str
    dm_application_denied_user: str
    dm_application_approved_admin: str
    dm_application_denied_admin: str
    dm_application_note_prompts: Dict[str, str]
    dm_application_note_confirmations: Dict[str, str]
    dm_application_note_skip_hint: str
    dm_application_note_skip_keyword: str
    dm_application_note_label: str
    dm_application_note_no_active: str
    dm_status_none: str
    dm_status_pending: str
    dm_status_approved: str
    dm_status_denied: str
    dm_status_withdrawn: str
    dm_status_unknown: str
    dm_status_template: str
    dm_status_template_with_note: str
    dm_status_last_updated_label: str
    dm_withdraw_success: str
    dm_withdraw_not_found: str
    dm_admin_added: str
    dm_admin_removed: str
    dm_not_owner: str
    dm_already_admin: str
    dm_not_admin: str
    dm_no_admins: str
    dm_cancelled: str
    dm_admin_enter_user_id: str
    dm_admin_invalid_user_id: str
    group_xp_updated: str
    group_xp_leaderboard_title: str
    group_cup_added: str
    group_cup_leaderboard_title: str
    group_no_data: str
    group_add_cup_usage: str
    group_add_cup_invalid_format: str
    group_add_xp_usage: str
    group_add_xp_success: str
    group_remove_xp_success: str
    group_promote_usage: str
    group_demote_usage: str
    group_promote_success: str
    group_demote_success: str
    group_promote_already: str
    group_demote_missing: str
    group_panel_intro: str
    group_panel_ban_button: str
    group_panel_mute_button: str
    group_panel_add_xp_button: str
    group_panel_manage_cups_button: str
    group_panel_manage_admins_button: str
    group_panel_settings_button: str
    group_panel_close_button: str
    group_panel_ban_prompt: str
    group_panel_mute_prompt: str
    group_panel_add_xp_prompt: str
    group_panel_remove_xp_prompt: str
    group_panel_cups_hint: str
    group_panel_admins_hint: str
    group_panel_settings_hint: str
    group_panel_closed: str
    group_panel_cancel_keyword: str
    group_panel_cancelled: str
    group_panel_invalid_target: str
    group_panel_action_error: str
    group_panel_ban_success: str
    group_panel_mute_success: str
    group_panel_help_button: str
    group_panel_refresh_button: str
    group_panel_overview_title: str
    group_panel_metric_tracked: str
    group_panel_metric_total_xp: str
    group_panel_metric_top_member: str
    group_panel_metric_top_member_empty: str
    group_panel_metric_cups: str
    group_panel_metric_admins: str
    group_panel_recent_cup: str
    group_panel_last_activity: str
    group_panel_unknown_chat: str
    group_panel_actions_hint: str
    group_panel_help_hint: str
    group_panel_menu_back_button: str
    group_panel_menu_ban_title: str
    group_panel_menu_ban_description: str
    group_panel_menu_ban_execute_button: str
    group_panel_menu_ban_help_button: str
    group_panel_menu_mute_title: str
    group_panel_menu_mute_description: str
    group_panel_menu_mute_execute_button: str
    group_panel_menu_mute_help_button: str
    group_panel_menu_xp_title: str
    group_panel_menu_xp_description: str
    group_panel_menu_xp_list_button: str
    group_panel_menu_xp_add_button: str
    group_panel_menu_xp_remove_button: str
    group_panel_menu_xp_members_header: str
    group_panel_menu_xp_members_entry: str
    group_panel_menu_xp_members_empty: str
    group_panel_menu_cups_title: str
    group_panel_menu_cups_description: str
    group_panel_menu_cups_latest_button: str
    group_panel_menu_cups_howto_button: str
    group_panel_menu_admins_title: str
    group_panel_menu_admins_description: str
    group_panel_menu_admins_list_button: str
    group_panel_menu_admins_list_header: str
    group_panel_menu_admins_list_entry: str
    group_panel_menu_admins_list_empty: str
    group_panel_menu_admins_list_unknown: str
    group_panel_menu_admins_howto_button: str
    group_panel_menu_settings_title: str
    group_panel_menu_settings_description: str
    group_panel_menu_settings_tools_button: str
    group_panel_menu_settings_help_button: str
    error_generic: str
    glass_panel_caption: str
    admin_list_header: str
    dm_rate_limited: str
    dm_language_button: str
    dm_language_menu_title: str
    dm_language_close_button: str
    dm_language_updated: str
    group_refresh_button: str
    dm_admin_panel_intro: str
    dm_admin_panel_view_applications_button: str
    dm_admin_panel_view_members_button: str
    dm_admin_panel_manage_admins_button: str
    dm_admin_panel_manage_questions_button: str
    dm_admin_panel_more_tools_button: str
    dm_admin_panel_insights_button: str
    dm_admin_panel_back_button: str
    dm_admin_panel_members_header: str
    dm_admin_panel_members_empty: str
    dm_admin_manage_title: str
    dm_admin_manage_intro: str
    dm_admin_manage_add_button: str
    dm_admin_manage_remove_button: str
    dm_admin_manage_list_button: str
    dm_admin_manage_back_button: str
    dm_admin_manage_list_header: str
    dm_admin_manage_list_empty: str
    dm_admin_manage_list_entry: str
    dm_admin_manage_list_unknown: str
    dm_admin_panel_add_admin_prompt: str
    dm_admin_panel_more_tools_text: str
    dm_admin_panel_more_tools_no_webapp: str
    dm_admin_questions_menu_title: str
    dm_admin_questions_menu_intro: str
    dm_admin_questions_role_label: str
    dm_admin_questions_goals_label: str
    dm_admin_questions_availability_label: str
    dm_admin_questions_followup_label_template: str
    dm_admin_questions_prompt: str
    dm_admin_questions_reset_keyword: str
    dm_admin_questions_reset_hint: str
    dm_admin_questions_success: str
    dm_admin_questions_reset_success: str
    dm_admin_questions_cancelled: str
    dm_admin_questions_back_button: str
    dm_admin_panel_insights_title: str
    dm_admin_panel_insights_counts: str
    dm_admin_panel_insights_languages: str
    dm_admin_panel_insights_languages_empty: str
    dm_admin_panel_insights_recent: str
    dm_admin_panel_insights_recent_empty: str
    group_help_intro: str
    group_help_member_title: str
    group_help_cmd_help: str
    group_help_cmd_myxp: str
    group_help_cmd_xp: str
    group_help_cmd_cups: str
    group_help_admin_title: str
    group_help_admin_hint: str
    group_help_cmd_panel: str
    group_help_cmd_add_cup: str
    group_help_cmd_addxp: str
    group_help_cmd_promote: str
    group_help_cmd_demote: str
    group_help_footer: str
    group_myxp_response: str
    group_myxp_no_data: str
    language_names: Dict[str, str]


PERSIAN_TEXTS = TextPack(
    dm_welcome=(
        "<b>🪟 سلام! خوشحالیم به پنل شیشه‌ای فلایزکس سر زدی.</b>\n\n"
        "برای شروع فقط روی دکمه پایین بزن تا درخواستت رو با هم جلو ببریم."
    ),
    dm_apply_button="شروع درخواست عضویت",
    dm_open_webapp_button="ورود به داشبورد وب",
    dm_admin_panel_button="رفتن به پنل ادمین",
    dm_status_button="دیدن وضعیت درخواست",
    dm_withdraw_button="انصراف از درخواست",
    dm_application_started=(
        "📝 بزن بریم! چند سوال کوتاه می‌پرسیم تا بهتر آشنات بشیم.\n"
        "هر وقت خواستی منصرف بشی، فقط /cancel رو بفرست."
    ),
    dm_application_question="۱️⃣ دوست داری تو گیلد چه نقشی داشته باشی؟",
    dm_application_received=(
        "✅ درخواستت رسید! بعد از بررسی بهت خبر می‌دیم.\n"
        "اگه خواستی پیگیری کنی، از دکمه «دیدن وضعیت درخواست» استفاده کن."
    ),
    dm_application_duplicate=(
        "ℹ️ درخواستت قبلاً ثبت شده و همین الان هم در حال بررسیه."
    ),
    dm_application_already_member=(
        "ℹ️ تو همین حالا عضو گیلدی و لازم نیست درخواست تازه‌ای بفرستی."
    ),
    dm_application_role_prompt="۱️⃣ دوست داری تو گیلد چه نقشی داشته باشی؟ (تاجر، مبارز، کاوشگر، پشتیبان)",
    dm_application_role_options={
        "trader": ["تاجر", "trader"],
        "fighter": ["مبارز", "fighter"],
        "explorer": ["کاوشگر", "explorer"],
        "support": ["پشتیبان", "support"],
    },
    dm_application_followup_prompts={
        "trader": "۲️⃣ از تجربه‌هات در معامله یا مدیریت منابع برامون بگو.",
        "fighter": "۲️⃣ چه سبکی از نبرد یا استراتژی برات جذابه؟",
        "explorer": "۲️⃣ چه جور ماجراجویی یا اکتشافی رو بیشتر دوست داری؟",
        "support": "۲️⃣ معمولاً چطور به هم‌تیمی‌هات نیرو می‌دی؟",
    },
    dm_application_goals_prompt="۳️⃣ با پیوستن به گیلد دنبال چه هدف یا تجربه‌ای هستی؟",
    dm_application_availability_prompt="۴️⃣ معمولاً کی‌ها آنلاین می‌شی یا فرصت همراهی داری؟",
    dm_application_summary_title="<b>📋 خلاصه جواب‌هات</b>",
    dm_application_summary_item="• <b>{question}</b>\n  {answer}",
    dm_application_invalid_choice="یکی از گزینه‌های پیشنهادی رو انتخاب کن: {options}",
    dm_admin_only="⛔️ این بخش مخصوص ادمین‌هاست.",
    dm_no_pending="فعلاً درخواستی برای بررسی نداریم.",
    dm_application_item=(
        "<b>کاربر:</b> {full_name} ({user_id})\n"
        "<b>نام کاربری:</b> {username}\n"
        "<b>پاسخ‌ها:</b>\n{answers}\n"
        "<b>زمان ثبت:</b> {created_at}"
    ),
    dm_application_action_buttons={
        "approve": "✅ تأیید",
        "deny": "❌ رد",
        "skip": "⏭ بعدی",
    },
    dm_application_approved_user="🎉 درخواستت تأیید شد! خوش اومدی به جمعمون.",
    dm_application_denied_user="❗️ این دفعه نشد، ولی ممنون که تلاش کردی.",
    dm_application_approved_admin="✅ درخواست کاربر با موفقیت تأیید شد.",
    dm_application_denied_admin="❌ درخواست کاربر رد شد.",
    dm_application_note_prompts={
        "approve": "✅ داری {full_name} ({user_id}) رو تأیید می‌کنی. یه پیام خوشامد یا توضیح کوتاه بنویس.",
        "deny": "❌ داری درخواست {full_name} ({user_id}) رو رد می‌کنی. لطفاً دلیل یا توضیح دوستانه‌ای بفرست.",
    },
    dm_application_note_confirmations={
        "approve": "✅ تأیید انجام شد و پیامش هم فرستاده شد.",
        "deny": "❌ رد درخواست انجام شد و پیام اطلاع‌رسانی هم ارسال شد.",
    },
    dm_application_note_skip_hint="اگر نمی‌خوای چیزی بنویسی، کلمه «صرفنظر» رو بفرست.",
    dm_application_note_skip_keyword="صرفنظر",
    dm_application_note_label="یادداشت",
    dm_application_note_no_active="ℹ️ الان موردی برای گذاشتن یادداشت نداریم.",
    dm_status_none="ℹ️ هنوز درخواستی ثبت نکردی.",
    dm_status_pending="در انتظار بررسی",
    dm_status_approved="تأیید شده",
    dm_status_denied="رد شده",
    dm_status_withdrawn="انصراف دادی",
    dm_status_unknown="نامشخص ({status})",
    dm_status_template=(
        "<b>وضعیت درخواستت:</b> {status}\n"
        "<i>{last_updated_label}: {updated_at}</i>"
    ),
    dm_status_template_with_note=(
        "<b>وضعیت درخواستت:</b> {status}\n"
        "<i>{last_updated_label}: {updated_at}</i>\n"
        "📝 {note}"
    ),
    dm_status_last_updated_label="آخرین بروزرسانی",
    dm_withdraw_success="♻️ درخواستت با موفقیت لغو شد.",
    dm_withdraw_not_found="درخواستی برای لغو پیدا نکردیم.",
    dm_admin_added="✅ کاربر {user_id} به جمع ادمین‌ها اضافه شد.",
    dm_admin_removed="♻️ کاربر {user_id} از فهرست ادمین‌ها خارج شد.",
    dm_not_owner="⛔️ فقط مالک ربات می‌تونه این دستور رو اجرا کنه.",
    dm_already_admin="ℹ️ کاربر {user_id} همین الان هم ادمینه.",
    dm_not_admin="ℹ️ کاربر {user_id} بین ادمین‌ها نیست.",
    dm_no_admins="فعلاً هیچ ادمینی ثبت نشده.",
    dm_cancelled="فرآیند درخواست متوقف شد.",
    dm_admin_enter_user_id="شناسه عددی کاربر رو بفرست.",
    dm_admin_invalid_user_id="شناسه باید حتماً عدد باشه.",
    group_xp_updated="✨ {full_name} الان {xp} امتیاز تجربه داره!",
    group_xp_leaderboard_title="🏆 جدول امتیاز اعضای فعال",
    group_cup_added="🏆 جام تازه‌ای با عنوان «{title}» ثبت شد.",
    group_cup_leaderboard_title="🥇 جدول افتخارات گیلد",
    group_no_data="هنوز چیزی ثبت نشده.",
    group_add_cup_usage="نحوه استفاده: /add_cup عنوان | توضیح | قهرمان,نایب‌قهرمان,سوم",
    group_add_cup_invalid_format="ساختار پیام درست نیست؛ با جداکننده | امتحان کن.",
    group_add_xp_usage="نحوه استفاده: /addxp شناسه‌کاربر مقدار (یا در پاسخ به پیام کاربر مقدار رو بفرست)",
    group_add_xp_success="✨ امتیاز {full_name} به {xp} رسید!",
    group_remove_xp_success="➖ امتیاز {full_name} به {xp} کاهش پیدا کرد.",
    group_promote_usage="برای اضافه کردن ادمین، شناسه رو بفرست یا به پیامش پاسخ بده.",
    group_demote_usage="برای حذف ادمین، شناسه رو بفرست یا به پیامش پاسخ بده.",
    group_promote_success="🛡️ {full_name} حالا دسترسی ادمین داره.",
    group_demote_success="♻️ دسترسی ادمین {full_name} برداشته شد.",
    group_promote_already="ℹ️ این کاربر قبلاً تو لیست ادمین‌هاست.",
    group_demote_missing="ℹ️ این کاربر تو لیست ادمین‌ها پیدا نشد.",
    group_panel_intro=(
        "<b>🛡️ کنترل‌پنل {chat_title}</b>\n"
        "همه‌چیز اینجاست؛ آمار گروه رو پایین ببین و از دکمه‌ها کمک بگیر."
    ),
    group_panel_ban_button="حذف از گروه",
    group_panel_mute_button="بی‌صدا",
    group_panel_add_xp_button="افزودن XP",
    group_panel_manage_cups_button="مدیریت جام‌ها",
    group_panel_manage_admins_button="ادمین‌ها",
    group_panel_settings_button="تنظیمات",
    group_panel_close_button="بستن پنل",
    group_panel_ban_prompt="برای حذف عضو، به پیامش پاسخ بده یا برای لغو «cancel» رو بفرست.",
    group_panel_mute_prompt="برای بی‌صدا کردن، به پیامش پاسخ بده یا «cancel» رو برای لغو بنویس.",
    group_panel_add_xp_prompt="به پیام عضو جواب بده و مقدار XP رو بفرست. برای لغو «cancel» کافیه.",
    group_panel_remove_xp_prompt="برای کم کردن XP، به پیام عضو جواب بده و مقدار رو بفرست. با «cancel» هم می‌تونی منصرف شی.",
    group_panel_cups_hint="برای ثبت جام جدید از دستور /add_cup کمک بگیر.",
    group_panel_admins_hint="برای مدیریت ادمین‌ها از /promote و /demote استفاده کن.",
    group_panel_settings_hint="برای تنظیمات بیشتر می‌تونی سر بزنی به پنل وب یا پیام خصوصی.",
    group_panel_closed="پنل بسته شد.",
    group_panel_cancel_keyword="cancel",
    group_panel_cancelled="✅ عملیات لغو شد.",
    group_panel_invalid_target="به پیام همون عضوی که مدنظرته جواب بده.",
    group_panel_action_error="⚠️ الان نشد انجام بدیم؛ کمی بعد دوباره امتحان کن.",
    group_panel_ban_success="🚫 {full_name} از گروه خارج شد.",
    group_panel_mute_success="🔇 {full_name} بی‌صدا شد.",
    group_panel_help_button="راهنما",
    group_panel_refresh_button="تازه‌سازی",
    group_panel_overview_title="📊 تصویر کلی گروه",
    group_panel_metric_tracked="• اعضای ثبت‌شده: <b>{members}</b>",
    group_panel_metric_total_xp="• مجموع XP ذخیره‌شده: <b>{total_xp}</b>",
    group_panel_metric_top_member="• فعال‌ترین عضو: <b>{name}</b> با <code>{xp}</code> XP",
    group_panel_metric_top_member_empty="• هنوز هیچ امتیاز تجربه‌ای ثبت نشده.",
    group_panel_metric_cups="• جام‌های ثبت‌شده: <b>{count}</b>",
    group_panel_metric_admins="• ادمین‌های ثبت‌شده: <b>{count}</b>",
    group_panel_recent_cup="• تازه‌ترین جام: <b>{title}</b> ({created_at})",
    group_panel_last_activity="• آخرین فعالیت: {timestamp}",
    group_panel_unknown_chat="گروه",
    group_panel_actions_hint="برای مدیریت سریع از دکمه‌های شیشه‌ای استفاده کن.",
    group_panel_help_hint="هر زمان نیاز به توضیح داشتی، روی «راهنما» بزن یا /help رو بفرست.",
    group_panel_menu_back_button="بازگشت به پنل",
    group_panel_menu_ban_title="🚫 حذف عضو از گروه",
    group_panel_menu_ban_description="یکی از گزینه‌های زیر رو انتخاب کن تا عضو موردنظر رو خارج کنی.",
    group_panel_menu_ban_execute_button="شروع حذف با پاسخ به پیام",
    group_panel_menu_ban_help_button="یادآوری روش حذف",
    group_panel_menu_mute_title="🔇 ساکت کردن عضو",
    group_panel_menu_mute_description="برای بی‌صدا کردن موقتی، از گزینه‌های پایین کمک بگیر.",
    group_panel_menu_mute_execute_button="شروع بی‌صدا کردن",
    group_panel_menu_mute_help_button="راهنمای بی‌صدا کردن",
    group_panel_menu_xp_title="✨ مدیریت XP اعضا",
    group_panel_menu_xp_description="می‌تونی لیست اعضای ثبت‌شده رو ببینی یا به سرعت امتیاز رو تغییر بدی.",
    group_panel_menu_xp_list_button="نمایش اعضای ثبت‌شده",
    group_panel_menu_xp_add_button="افزایش XP",
    group_panel_menu_xp_remove_button="کاهش XP",
    group_panel_menu_xp_members_header="📋 لیست ۱۰ عضو برتر ({count} نفر):\n{members}",
    group_panel_menu_xp_members_entry="{index}. <b>{name}</b> — <code>{xp}</code> XP",
    group_panel_menu_xp_members_empty="فعلاً هیچ امتیازی برای اعضا ثبت نشده.",
    group_panel_menu_cups_title="🏆 ابزارهای مدیریت جام",
    group_panel_menu_cups_description="سریع آخرین جام‌ها رو ببین یا یادت بندازیم چطور جام جدید ثبت کنی.",
    group_panel_menu_cups_latest_button="نمایش آخرین جام‌ها",
    group_panel_menu_cups_howto_button="راهنمای ثبت جام",
    group_panel_menu_admins_title="🛡️ مدیریت لیست ادمین‌ها",
    group_panel_menu_admins_description="لیست فعلی رو ببین یا دستورهای ارتقا و عزل رو یادآوری کن.",
    group_panel_menu_admins_list_button="نمایش ادمین‌های ثبت‌شده",
    group_panel_menu_admins_list_header="🛡️ ادمین‌های ثبت‌شده ({count} نفر):\n{admins}",
    group_panel_menu_admins_list_entry="• <b>{display}</b> — <code>{user_id}</code>",
    group_panel_menu_admins_list_empty="فعلاً هیچ ادمینی ثبت نشده.",
    group_panel_menu_admins_list_unknown="کاربر ناشناس",
    group_panel_menu_admins_howto_button="راهنمای مدیریت ادمین‌ها",
    group_panel_menu_settings_title="⚙️ تنظیمات و ابزارهای بیشتر",
    group_panel_menu_settings_description="برای تغییرات عمیق‌تر می‌تونی از ابزارهای پیشنهادی زیر کمک بگیری.",
    group_panel_menu_settings_tools_button="باز کردن ابزارهای بیشتر",
    group_panel_menu_settings_help_button="راهنمای تنظیمات",
    error_generic="⚠️ اوه! مشکلی پیش اومد، یک بار دیگه تلاش کن.",
    glass_panel_caption=(
        "<i>یک تجربه شیشه‌ای با پس‌زمینه مه‌آلود و دکمه‌های درخشان که حس صمیمیت می‌ده.</i>"
    ),
    admin_list_header="👮‍♂️ ادمین‌های فعال:\n{admins}",
    dm_rate_limited="⏳ چند لحظه صبر کن؛ درخواست‌هات پشت سر هم بوده.",
    dm_language_button="تغییر زبان",
    dm_language_menu_title="زبان دلخواهت رو انتخاب کن:",
    dm_language_close_button="بازگشت",
    dm_language_updated="✅ زبان ربات عوض شد.",
    group_refresh_button="🔄 تازه‌سازی",
    dm_admin_panel_intro=(
        "<b>🛡️ خوش اومدی به پنل مدیریت فلایزکس</b>\n"
        "هر گزینه‌ای که لازمت هست رو از دکمه‌های زیر انتخاب کن."
    ),
    dm_admin_panel_view_applications_button="درخواست‌های در صف",
    dm_admin_panel_view_members_button="اعضای تاییدشده",
    dm_admin_panel_manage_admins_button="ادمین‌ها را مدیریت کن",
    dm_admin_panel_manage_questions_button="ویرایش سوال‌ها",
    dm_admin_panel_more_tools_button="ابزارهای بیشتر",
    dm_admin_panel_insights_button="گزارش‌ها و آمار",
    dm_admin_panel_back_button="بازگشت به پیام خوش‌آمد",
    dm_admin_panel_members_header="✅ اعضای تاییدشده ({count} نفر):\n{members}",
    dm_admin_panel_members_empty="فعلاً هیچ عضوی تایید نشده.",
    dm_admin_manage_title="<b>🛡️ مدیریت ادمین‌ها</b>",
    dm_admin_manage_intro="برای اضافه، حذف یا دیدن فهرست ادمین‌ها از دکمه‌های پایین کمک بگیر.",
    dm_admin_manage_add_button="اضافه کردن ادمین",
    dm_admin_manage_remove_button="حذف ادمین",
    dm_admin_manage_list_button="مشاهده فهرست",
    dm_admin_manage_back_button="برگشت به پنل اصلی",
    dm_admin_manage_list_header="<b>ادمین‌های فعال:</b>",
    dm_admin_manage_list_empty="فعلاً ادمینی تعریف نشده.",
    dm_admin_manage_list_entry="• {display} — شناسه: <code>{user_id}</code>",
    dm_admin_manage_list_unknown="بدون نام",
    dm_admin_panel_add_admin_prompt="شناسه عددی کاربر مدنظر رو بفرست.",
    dm_admin_panel_more_tools_text=(
        "✨ برای مدیریت کامل‌تر می‌تونی از نسخه وب استفاده کنی:\n"
        "<a href=\"{webapp_url}\">رفتن به داشبورد</a>"
    ),
    dm_admin_panel_more_tools_no_webapp=(
        "ℹ️ هنوز آدرس وب‌اپ مشخص نشده. لطفاً مقدار webapp_url رو در پیکربندی تنظیم کن."
    ),
    dm_admin_questions_menu_title="<b>مدیریت سوال‌های فرم ({language})</b>",
    dm_admin_questions_menu_intro=(
        "سوالی که می‌خوای ویرایش کنی رو انتخاب کن.\n"
        "اگه نظرت عوض شد، حین ویرایش کلمه «{reset_keyword}» رو بفرست تا متن اولیه برگرده."
    ),
    dm_admin_questions_role_label="سوال نقش (مرحله ۱)",
    dm_admin_questions_goals_label="سوال هدف‌ها (مرحله ۳)",
    dm_admin_questions_availability_label="سوال زمان حضور (مرحله ۴)",
    dm_admin_questions_followup_label_template="سوال تکمیلی ({role})",
    dm_admin_questions_prompt=(
        "متن تازه برای «{label}» رو بفرست.\n"
        "برای برگشت به حالت اولیه، فقط «{reset_keyword}» رو بفرست.\n\n"
        "متن فعلی:\n{current}"
    ),
    dm_admin_questions_reset_keyword="پیشفرض",
    dm_admin_questions_reset_hint="ارسال «{reset_keyword}» سوال رو به متن اصلی برمی‌گردونه.",
    dm_admin_questions_success="سوال «{label}» به‌روزرسانی شد.",
    dm_admin_questions_reset_success="سوال «{label}» به متن اولیه برگشت.",
    dm_admin_questions_cancelled="ویرایش سوال لغو شد.",
    dm_admin_questions_back_button="بازگشت",
    dm_admin_panel_insights_title="<b>📊 داشبورد مدیریتی</b>",
    dm_admin_panel_insights_counts=(
        "• در انتظار بررسی: {pending}\n"
        "• تأیید شده: {approved}\n"
        "• رد شده: {denied}\n"
        "• لغو شده: {withdrawn}\n"
        "• مجموع درخواست‌ها: {total}\n"
        "• میانگین طول پاسخ‌های در انتظار: {average_length:.0f} کاراکتر"
    ),
    dm_admin_panel_insights_languages="<b>🌐 زبان‌های محبوب:</b>\n{languages}",
    dm_admin_panel_insights_languages_empty="فعلاً کسی زبان دلخواهش رو ثبت نکرده.",
    dm_admin_panel_insights_recent="<b>🕒 آخرین رویدادها:</b>\n{items}",
    dm_admin_panel_insights_recent_empty="چیزی برای نمایش وجود نداره.",
    group_help_intro="راهنمای سریع دستورات گروه برای اعضا و ادمین‌ها.",
    group_help_member_title="🎯 دستورات در دسترس همه",
    group_help_cmd_help="نمایش همین راهنما.",
    group_help_cmd_myxp="دیدن XP فعلی خودت.",
    group_help_cmd_xp="مشاهدهٔ جدول XP گروه.",
    group_help_cmd_cups="مشاهدهٔ افتخارات و جام‌های ثبت‌شده.",
    group_help_admin_title="🛠️ دستورات مخصوص ادمین‌ها",
    group_help_admin_hint="دستورات زیر نیاز به دسترسی ادمین دارند.",
    group_help_cmd_panel="باز کردن کنترل‌پنل شیشه‌ای در گروه.",
    group_help_cmd_add_cup="ثبت یک جام تازه با عنوان، توضیح و سکوها.",
    group_help_cmd_addxp="افزودن XP دستی برای اعضا.",
    group_help_cmd_promote="اضافه کردن ادمین جدید.",
    group_help_cmd_demote="حذف یک ادمین از لیست.",
    group_help_footer="برای ابزارهای بیشتر به وب‌اپ سر بزن یا از دکمهٔ تنظیمات استفاده کن.",
    group_myxp_response="✨ {full_name} الان <b>{xp}</b> XP داره.",
    group_myxp_no_data="هنوز هیچ XP برای تو ثبت نشده.",
    language_names={
        "fa": "فارسی",
        "en": "انگلیسی",
    },
)


ENGLISH_TEXTS = TextPack(
    dm_welcome=(
        "<b>🪟 Hey there! Thanks for dropping by the Flyzex glass panel.</b>\n\n"
        "Tap the button below and we'll walk through your guild application together."
    ),
    dm_apply_button="Start guild application",
    dm_open_webapp_button="Open web dashboard",
    dm_admin_panel_button="Go to admin panel",
    dm_status_button="Check my status",
    dm_withdraw_button="Cancel my application",
    dm_application_started=(
        "📝 Let's do this! A few quick questions will help us get to know you.\n"
        "Need to stop? Send /cancel anytime."
    ),
    dm_application_question="1️⃣ What role feels most like you in the guild?",
    dm_application_received=(
        "✅ Got it! Your application is in and we'll let you know once it's reviewed.\n"
        "Use “Check my status” whenever you need an update."
    ),
    dm_application_duplicate=(
        "ℹ️ We already have an application from you and it's in the review queue."
    ),
    dm_application_already_member=(
        "ℹ️ You're already part of the guild—no need to apply again."
    ),
    dm_application_role_prompt="1️⃣ What role feels most like you in the guild? (Trader, Fighter, Explorer, Support)",
    dm_application_role_options={
        "trader": ["trader", "merchant"],
        "fighter": ["fighter", "warrior"],
        "explorer": ["explorer", "scout"],
        "support": ["support", "healer"],
    },
    dm_application_followup_prompts={
        "trader": "2️⃣ Tell us about your experience trading or managing resources.",
        "fighter": "2️⃣ What kind of combat style or strategy energizes you?",
        "explorer": "2️⃣ Share an adventure or discovery that stuck with you.",
        "support": "2️⃣ How do you usually lift up or support your squad?",
    },
    dm_application_goals_prompt="3️⃣ What are you hoping to get out of joining the guild?",
    dm_application_availability_prompt="4️⃣ When are you usually around to jump in?",
    dm_application_summary_title="<b>📋 Quick recap of your answers</b>",
    dm_application_summary_item="• <b>{question}</b>\n  {answer}",
    dm_application_invalid_choice="Pick one of the suggested options: {options}",
    dm_admin_only="⛔️ This area is just for admins.",
    dm_no_pending="No applications are waiting right now.",
    dm_application_item=(
        "<b>Applicant:</b> {full_name} ({user_id})\n"
        "<b>Username:</b> {username}\n"
        "<b>Answers:</b>\n{answers}\n"
        "<b>Submitted:</b> {created_at}"
    ),
    dm_application_action_buttons={
        "approve": "✅ Approve",
        "deny": "❌ Decline",
        "skip": "⏭ Next",
    },
    dm_application_approved_user="🎉 You're in! Welcome to the guild.",
    dm_application_denied_user="❗️ Not this time, but thanks for giving it a shot.",
    dm_application_approved_admin="✅ The application has been approved.",
    dm_application_denied_admin="❌ The application has been declined.",
    dm_application_note_prompts={
        "approve": "✅ You're welcoming {full_name} ({user_id}). Send a warm note or a quick reason.",
        "deny": "❌ You're declining {full_name} ({user_id}). Please share a short, helpful reason.",
    },
    dm_application_note_confirmations={
        "approve": "✅ Approval sent and the applicant has been notified.",
        "deny": "❌ Decline recorded and the applicant has been informed.",
    },
    dm_application_note_skip_hint="Type SKIP if you'd rather continue without a note.",
    dm_application_note_skip_keyword="skip",
    dm_application_note_label="Note",
    dm_application_note_no_active="ℹ️ There's no application waiting for a note right now.",
    dm_status_none="ℹ️ You haven't submitted an application yet.",
    dm_status_pending="In review",
    dm_status_approved="Approved",
    dm_status_denied="Declined",
    dm_status_withdrawn="Withdrawn",
    dm_status_unknown="Unknown ({status})",
    dm_status_template=(
        "<b>Your application status:</b> {status}\n"
        "<i>{last_updated_label}: {updated_at}</i>"
    ),
    dm_status_template_with_note=(
        "<b>Your application status:</b> {status}\n"
        "<i>{last_updated_label}: {updated_at}</i>\n"
        "📝 {note}"
    ),
    dm_status_last_updated_label="Last update",
    dm_withdraw_success="♻️ Your application has been cancelled.",
    dm_withdraw_not_found="We couldn't find an application to cancel.",
    dm_admin_added="✅ User {user_id} is now part of the admin team.",
    dm_admin_removed="♻️ User {user_id} has been removed from the admin team.",
    dm_not_owner="⛔️ Only the bot owner can run this command.",
    dm_already_admin="ℹ️ User {user_id} is already on the admin list.",
    dm_not_admin="ℹ️ User {user_id} isn't on the admin list.",
    dm_no_admins="No admins have been added yet.",
    dm_cancelled="The application flow has been stopped.",
    dm_admin_enter_user_id="Send the member's numeric ID.",
    dm_admin_invalid_user_id="The ID needs to be a number.",
    group_xp_updated="✨ {full_name} now has {xp} XP!",
    group_xp_leaderboard_title="🏆 XP board for active members",
    group_cup_added="🏆 Logged a new cup named “{title}”.",
    group_cup_leaderboard_title="🥇 Guild trophy board",
    group_no_data="Nothing has been recorded yet.",
    group_add_cup_usage="How to use: /add_cup Title | Description | Champion,Runner-up,Third",
    group_add_cup_invalid_format="That format doesn't look right—use the | separator.",
    group_add_xp_usage="How to use: /addxp user_id amount (or reply to their message with the amount)",
    group_add_xp_success="✨ {full_name}'s XP now sits at {xp}!",
    group_remove_xp_success="➖ {full_name}'s XP has been reduced to {xp}.",
    group_promote_usage="To add an admin, send their ID or reply to one of their messages.",
    group_demote_usage="To remove an admin, send their ID or reply to one of their messages.",
    group_promote_success="🛡️ {full_name} now has admin access.",
    group_demote_success="♻️ {full_name} is no longer an admin.",
    group_promote_already="ℹ️ That member is already on the admin team.",
    group_demote_missing="ℹ️ That member isn't listed as an admin.",
    group_panel_intro=(
        "<b>🛡️ {chat_title} control panel</b>\n"
        "Check the snapshot below and use the glass buttons for quick actions."
    ),
    group_panel_ban_button="Remove member",
    group_panel_mute_button="Mute",
    group_panel_add_xp_button="Add XP",
    group_panel_manage_cups_button="Manage cups",
    group_panel_manage_admins_button="Admins",
    group_panel_settings_button="Settings",
    group_panel_close_button="Close panel",
    group_panel_ban_prompt="Reply to the member you want to remove, or type 'cancel' to back out.",
    group_panel_mute_prompt="Reply to the member you want to mute, or type 'cancel' to back out.",
    group_panel_add_xp_prompt="Reply to the member and send the XP amount. Type 'cancel' to back out.",
    group_panel_remove_xp_prompt="Reply to the member and send the amount you want to subtract. Type 'cancel' to back out.",
    group_panel_cups_hint="Use /add_cup to log a new trophy run.",
    group_panel_admins_hint="Use /promote and /demote to adjust admin roles.",
    group_panel_settings_hint="For deeper settings, open the web dashboard or DM panel.",
    group_panel_closed="Panel closed.",
    group_panel_cancel_keyword="cancel",
    group_panel_cancelled="✅ Action cancelled.",
    group_panel_invalid_target="Reply directly to the member you're targeting.",
    group_panel_action_error="⚠️ Couldn't finish that right now—please try again shortly.",
    group_panel_ban_success="🚫 {full_name} has been removed from the group.",
    group_panel_mute_success="🔇 {full_name} has been muted.",
    group_panel_help_button="Help",
    group_panel_refresh_button="Refresh",
    group_panel_overview_title="📊 Group snapshot",
    group_panel_metric_tracked="• Members tracked: <b>{members}</b>",
    group_panel_metric_total_xp="• Total stored XP: <b>{total_xp}</b>",
    group_panel_metric_top_member="• Top member: <b>{name}</b> with <code>{xp}</code> XP",
    group_panel_metric_top_member_empty="• No XP has been recorded yet.",
    group_panel_metric_cups="• Cups logged: <b>{count}</b>",
    group_panel_metric_admins="• Admins on record: <b>{count}</b>",
    group_panel_recent_cup="• Latest cup: <b>{title}</b> ({created_at})",
    group_panel_last_activity="• Last recorded activity: {timestamp}",
    group_panel_unknown_chat="the guild",
    group_panel_actions_hint="Use the glass buttons below for quick moderation actions.",
    group_panel_help_hint="Need details? Tap Help or send /help anytime.",
    group_panel_menu_back_button="Back to panel",
    group_panel_menu_ban_title="🚫 Remove a member",
    group_panel_menu_ban_description="Pick one of the tools below to remove a member safely.",
    group_panel_menu_ban_execute_button="Start removal by replying",
    group_panel_menu_ban_help_button="Removal instructions",
    group_panel_menu_mute_title="🔇 Silence a member",
    group_panel_menu_mute_description="Temporarily restrict a member using the shortcuts below.",
    group_panel_menu_mute_execute_button="Start muting",
    group_panel_menu_mute_help_button="Muting instructions",
    group_panel_menu_xp_title="✨ XP management tools",
    group_panel_menu_xp_description="Review tracked members or adjust their XP right from here.",
    group_panel_menu_xp_list_button="Show tracked members",
    group_panel_menu_xp_add_button="Increase XP",
    group_panel_menu_xp_remove_button="Decrease XP",
    group_panel_menu_xp_members_header="📋 Top 10 tracked members ({count} total):\n{members}",
    group_panel_menu_xp_members_entry="{index}. <b>{name}</b> — <code>{xp}</code> XP",
    group_panel_menu_xp_members_empty="No XP has been recorded for members yet.",
    group_panel_menu_cups_title="🏆 Cup management tools",
    group_panel_menu_cups_description="Quickly review recent cups or revisit how to log a new one.",
    group_panel_menu_cups_latest_button="Show latest cups",
    group_panel_menu_cups_howto_button="Cup logging guide",
    group_panel_menu_admins_title="🛡️ Admin roster tools",
    group_panel_menu_admins_description="Check who's on the team or refresh the promote/demote steps.",
    group_panel_menu_admins_list_button="Show tracked admins",
    group_panel_menu_admins_list_header="🛡️ Recorded admins ({count}):\n{admins}",
    group_panel_menu_admins_list_entry="• <b>{display}</b> — <code>{user_id}</code>",
    group_panel_menu_admins_list_empty="No admins have been recorded yet.",
    group_panel_menu_admins_list_unknown="Unknown member",
    group_panel_menu_admins_howto_button="Admin management guide",
    group_panel_menu_settings_title="⚙️ Settings & extra tools",
    group_panel_menu_settings_description="Use the quick links below to jump into deeper configuration.",
    group_panel_menu_settings_tools_button="Open advanced tools",
    group_panel_menu_settings_help_button="Settings guide",
    error_generic="⚠️ Oops, something went wrong. Please try again.",
    glass_panel_caption=(
        "<i>A cozy glassmorphism experience with soft blur and vibrant buttons to keep things welcoming.</i>"
    ),
    admin_list_header="👮‍♂️ Current admins:\n{admins}",
    dm_rate_limited="⏳ Easy there! Give it a moment before sending more requests.",
    dm_language_button="Change language",
    dm_language_menu_title="Pick the language you prefer:",
    dm_language_close_button="Back",
    dm_language_updated="✅ Language updated.",
    group_refresh_button="🔄 Refresh",
    dm_admin_panel_intro=(
        "<b>🛡️ Welcome to the Flyzex admin panel</b>\n"
        "Grab whatever you need from the buttons below."
    ),
    dm_admin_panel_view_applications_button="Pending applications",
    dm_admin_panel_view_members_button="Approved members",
    dm_admin_panel_manage_admins_button="Manage admins",
    dm_admin_panel_manage_questions_button="Edit questions",
    dm_admin_panel_more_tools_button="More tools",
    dm_admin_panel_insights_button="Reports & insights",
    dm_admin_panel_back_button="Back to welcome",
    dm_admin_panel_members_header="✅ Approved members ({count}):\n{members}",
    dm_admin_panel_members_empty="No members have been approved yet.",
    dm_admin_manage_title="<b>🛡️ Admin management</b>",
    dm_admin_manage_intro="Use the buttons below to add, remove, or review the admin list.",
    dm_admin_manage_add_button="Add an admin",
    dm_admin_manage_remove_button="Remove an admin",
    dm_admin_manage_list_button="View admin list",
    dm_admin_manage_back_button="Back to main panel",
    dm_admin_manage_list_header="<b>Current admins:</b>",
    dm_admin_manage_list_empty="No admins have been registered yet.",
    dm_admin_manage_list_entry="• {display} — ID: <code>{user_id}</code>",
    dm_admin_manage_list_unknown="No name",
    dm_admin_panel_add_admin_prompt=(
        "Send the numeric ID of the member you'd like to promote."
        "\nSend /cancel if you change your mind."
    ),
    dm_admin_panel_more_tools_text=(
        "✨ Want the full toolkit? Hop into the web dashboard:\n"
        "<a href=\"{webapp_url}\">Open dashboard</a>"
    ),
    dm_admin_panel_more_tools_no_webapp=(
        "ℹ️ Add a webapp_url in settings.yaml to enable the web dashboard."
    ),
    dm_admin_questions_menu_title="<b>Manage application questions ({language})</b>",
    dm_admin_questions_menu_intro=(
        "Pick the question you want to update.\n"
        "While editing, type “{reset_keyword}” to bring back the default text."
    ),
    dm_admin_questions_role_label="Role question (step 1)",
    dm_admin_questions_goals_label="Goals question (step 3)",
    dm_admin_questions_availability_label="Availability question (step 4)",
    dm_admin_questions_followup_label_template="Follow-up question ({role})",
    dm_admin_questions_prompt=(
        "Send the new wording for “{label}”.\n"
        "If you change your mind, send “{reset_keyword}” to restore the default.\n\n"
        "Current text:\n{current}"
    ),
    dm_admin_questions_reset_keyword="reset",
    dm_admin_questions_reset_hint="Sending “{reset_keyword}” restores this question to its original wording.",
    dm_admin_questions_success="“{label}” has been updated.",
    dm_admin_questions_reset_success="“{label}” is back to the default text.",
    dm_admin_questions_cancelled="Question editing cancelled.",
    dm_admin_questions_back_button="Back",
    dm_admin_panel_insights_title="<b>📊 Admin dashboard</b>",
    dm_admin_panel_insights_counts=(
        "• In review: {pending}\n"
        "• Approved: {approved}\n"
        "• Declined: {denied}\n"
        "• Withdrawn: {withdrawn}\n"
        "• Total submissions: {total}\n"
        "• Avg. pending answer length: {average_length:.0f} characters"
    ),
    dm_admin_panel_insights_languages="<b>🌐 Preferred languages:</b>\n{languages}",
    dm_admin_panel_insights_languages_empty="No language preferences have been recorded yet.",
    dm_admin_panel_insights_recent="<b>🕒 Recent activity:</b>\n{items}",
    dm_admin_panel_insights_recent_empty="Nothing to show just yet.",
    group_help_intro="A quick reference of group commands for members and admins.",
    group_help_member_title="🎯 Commands available to everyone",
    group_help_cmd_help="Display this cheat sheet.",
    group_help_cmd_myxp="Show your current XP.",
    group_help_cmd_xp="Open the group XP leaderboard.",
    group_help_cmd_cups="Open the cups and trophies board.",
    group_help_admin_title="🛠️ Admin-only shortcuts",
    group_help_admin_hint="You need admin rights to run the commands below.",
    group_help_cmd_panel="Open the glass control panel inside the chat.",
    group_help_cmd_add_cup="Register a new cup with title, description, and podium.",
    group_help_cmd_addxp="Manually grant XP to a member.",
    group_help_cmd_promote="Promote a member to admin.",
    group_help_cmd_demote="Remove someone from the admin list.",
    group_help_footer="For deeper controls, jump into the web dashboard or the DM admin panel.",
    group_myxp_response="✨ {full_name} currently has <b>{xp}</b> XP.",
    group_myxp_no_data="You don't have any XP in this chat yet.",
    language_names={
        "fa": "Persian",
        "en": "English",
    },
)


DEFAULT_LANGUAGE_CODE = "fa"

_TEXT_PACKS: Dict[str, TextPack] = {
    "fa": PERSIAN_TEXTS,
    "en": ENGLISH_TEXTS,
}

AVAILABLE_LANGUAGE_CODES = tuple(_TEXT_PACKS.keys())


def get_default_text_pack() -> TextPack:
    """Return the text pack for the configured default language."""

    return _TEXT_PACKS[DEFAULT_LANGUAGE_CODE]


def normalize_language_code(language_code: str | None) -> str | None:
    if not language_code:
        return None
    code = language_code.replace("_", "-").strip()
    if not code:
        return None
    primary = code.split("-", 1)[0].strip().lower()
    return primary or None


def get_text_pack(language_code: str | None) -> TextPack:
    normalised = normalize_language_code(language_code)
    if normalised and normalised in _TEXT_PACKS:
        return _TEXT_PACKS[normalised]
    return get_default_text_pack()

