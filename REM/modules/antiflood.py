import html
from typing import Optional, List
import re

from telegram import Message, Chat, Update, User, ChatPermissions

from SaitamaRobot import TIGERS, WOLVES, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import antiflood_sql as sql
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.connection import connected
from SaitamaRobot.modules.helper_funcs.alternate import send_message
from SaitamaRobot.modules.sql.approve_sql import is_approved

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # تجاهل القنوات
        return ""

    # تجاهل المشرفين والقائمة البيضاء
    if is_user_admin(chat, user.id) or user.id in WOLVES or user.id in TIGERS:
        sql.update_flood(chat.id, None)
        return ""
    # تجاهل المستخدمين المعتمدين
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return
    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = "محظور"
            tag = "حظر"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "مطرود"
            tag = "طرد"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id, user.id, permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "مسكوت"
            tag = "إسكات"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "محظور لمدة {}".format(getvalue)
            tag = "حظر_مؤقت"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "مسكوت لمدة {}".format(getvalue)
            tag = "إسكات_مؤقت"
        send_message(
            update.effective_message, "بيب بوب!\n{}!".format(execstrings),
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>المستخدم:</b> {}"
            "\nتجاوز حد الرسائل في القروب.".format(
                html.escape(chat.title),
                tag,
                mention_html(user.id, html.escape(user.first_name)),
            )
        )

    except BadRequest:
        msg.reply_text(
            "ما أقدر أقيّد أحد هنا، عطيني الصلاحيات أول! بوقف مكافحة الإسبام بالوقت الحالي.",
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#معلومة"
            "\nما عندي صلاحية كافية لتقييد المستخدمين، انقطع مكافحة الإسبام تلقائياً".format(
                chat.title,
            )
        )


@run_async
@user_admin_no_reply
@bot_admin
def flood_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            update.effective_message.edit_text(
                f"رُفع الإسكات بواسطة {mention_html(user.id, html.escape(user.first_name))}.",
                parse_mode="HTML",
            )
        except:
            pass


@run_async
@user_admin
@loggable
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "هذا الأمر يشتغل بالقروبات بس، مو بالخاص",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat_id, 0)
            if conn:
                text = message.reply_text(
                    "انقطع مكافحة الإسبام في {}.".format(chat_name),
                )
            else:
                text = message.reply_text("انقطع مكافحة الإسبام.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "انقطع مكافحة الإسبام في {}.".format(chat_name),
                    )
                else:
                    text = message.reply_text("انقطع مكافحة الإسبام.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>المشرف:</b> {}"
                    "\nانقطع مكافحة الإسبام.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                    )
                )

            elif amount <= 3:
                send_message(
                    update.effective_message,
                    "مكافحة الإسبام لازم تكون 0 (معطلة) أو رقم أكبر من 3!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = message.reply_text(
                        "انضبط حد مكافحة الإسبام على {} في القروب: {}".format(
                            amount, chat_name,
                        ),
                    )
                else:
                    text = message.reply_text(
                        "تم تحديث حد مكافحة الإسبام إلى {}!".format(amount),
                    )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>المشرف:</b> {}"
                    "\nانضبط مكافحة الإسبام على <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                        amount,
                    )
                )

        else:
            message.reply_text("وسيط غير صحيح، استخدم رقم أو 'off'/'no'")
    else:
        message.reply_text(
            "استخدم `/setflood رقم` لتفعيل مكافحة الإسبام.\nأو استخدم `/setflood off` لتعطيلها!",
            parse_mode="markdown",
        )
    return ""


@run_async
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "هذا الأمر يشتغل بالقروبات بس، مو بالخاص",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = msg.reply_text(
                "ما أطبّق أي قيود إسبام في {}!".format(chat_name),
            )
        else:
            text = msg.reply_text("ما أطبّق أي قيود إسبام هنا!")
    else:
        if conn:
            text = msg.reply_text(
                "أقيّد الأعضاء بعد {} رسالة متتالية في {}.".format(
                    limit, chat_name,
                ),
            )
        else:
            text = msg.reply_text(
                "أقيّد الأعضاء بعد {} رسالة متتالية.".format(
                    limit,
                ),
            )


@run_async
@user_admin
def set_flood_mode(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "هذا الأمر يشتغل بالقروبات بس، مو بالخاص",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "حظر"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "طرد"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "إسكات"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """يبدو إنك تحاول تضبط وقت للحظر المؤقت بس ما حددت المدة؛ جرب: `/setfloodmode tban <المدة>`.
أمثلة على المدة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "حظر مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """يبدو إنك تحاول تضبط وقت للإسكات المؤقت بس ما حددت المدة؛ جرب: `/setfloodmode tmute <المدة>`.
أمثلة على المدة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "إسكات مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message, "ما أفهم إلا: ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = msg.reply_text(
                "تجاوز حد الإسبام راح يؤدي إلى {} في {}!".format(
                    settypeflood, chat_name,
                ),
            )
        else:
            text = msg.reply_text(
                "تجاوز حد الإسبام راح يؤدي إلى {}!".format(
                    settypeflood,
                ),
            )
        return (
            "<b>{}:</b>\n"
            "<b>المشرف:</b> {}\n"
            "غيّر وضع مكافحة الإسبام. سيتم {} للمستخدم.".format(
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
                settypeflood,
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "حظر"
        elif getmode == 2:
            settypeflood = "طرد"
        elif getmode == 3:
            settypeflood = "إسكات"
        elif getmode == 4:
            settypeflood = "حظر مؤقت لمدة {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "إسكات مؤقت لمدة {}".format(getvalue)
        if conn:
            text = msg.reply_text(
                "إرسال رسائل أكثر من الحد راح يؤدي إلى {} في {}.".format(
                    settypeflood, chat_name,
                ),
            )
        else:
            text = msg.reply_text(
                "إرسال رسائل أكثر من الحد راح يؤدي إلى {}.".format(
                    settypeflood,
                ),
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "مو مفعّل مكافحة الإسبام."
    else:
        return "مكافحة الإسبام مضبوطة على `{}`.".format(limit)


__help__ = """

  مكافحة الإسبام تتيح لك اتخاذ إجراء على المستخدمين الذين يرسلون أكثر من x رسالة متتالية. تجاوز الحد المحدد   سيؤدي إلى تقييد ذلك المستخدم.
   هذا سيسكت المستخدمين إذا أرسلوا أكثر من 10 رسائل متتالية، ويتم تجاهل البوتات.
   • `/flood`*:* عرض إعداد مكافحة الإسبام الحالي
  • *للمشرفين فقط:*
   • `/setflood <رقم/'no'/'off'>`*:* تفعيل أو تعطيل مكافحة الإسبام
   *مثال:* `/setflood 10`
   • `/setfloodmode <ban/kick/mute/tban/tmute> <القيمة>`*:* الإجراء المتخذ عند تجاوز المستخدم الحد. ban/kick/mute/tmute/tban
  • *ملاحظة:*
   • يجب تحديد القيمة لـ tban و tmute!!
   يمكن أن تكون:
   `5m` = 5 دقائق
   `6h` = 6 ساعات
   `3d` = 3 أيام
   `1w` = أسبوع واحد
   """

__mod_name__ = "مكافحة الإسبام"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.group, check_flood,
)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, filters=Filters.group)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode,
)  # , filters=Filters.group)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(flood_button, pattern=r"unmute_flooder")
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(FLOOD_QUERY_HANDLER)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__handlers__ = [
    (FLOOD_BAN_HANDLER, FLOOD_GROUP),
    SET_FLOOD_HANDLER,
    FLOOD_HANDLER,
    SET_FLOOD_MODE_HANDLER,
]
