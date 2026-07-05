import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, run_async
from telegram.utils.helpers import mention_html

import SaitamaRobot.modules.sql.global_bans_sql as sql
from SaitamaRobot import (
    DEV_USERS,
    DRAGONS,
    DEMONS,
    EVENT_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    SUPPORT_CHAT,
    TIGERS,
    WOLVES,
    dispatcher,
)
from SaitamaRobot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from SaitamaRobot.modules.sql.users_sql import get_user_com_chats
from SaitamaRobot.modules.helper_funcs.alternate import send_to_list

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "لا يبدو أنك تشير إلى مستخدم أو أن الآيدي المحدد غير صحيح..",
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "هذا المستخدم من الرابطة، ما أقدر أتصرف ضد واحد منا.",
        )
        return

    if int(user_id) in DRAGONS:
        message.reply_text(
            "أوه أوه، أحد يحاول يحظر كارثة مستوى التنين! *يجيب الپاپكورن*",
        )
        return

    if int(user_id) in DEMONS:
        message.reply_text(
            "أوه أوه، أحد يحاول يحظر كارثة مستوى الشيطان! *يجيب الپاپكورن*",
        )
        return

    if int(user_id) in TIGERS:
        message.reply_text("هذا نمر! ما ينحظر!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("هذا ذئب! ما ينحظر!")
        return

    if user_id == bot.id:
        message.reply_text("تريد أضرب نفسي؟")
        return

    if int(user_id) in [777000, 1087968824]:
        message.reply_text("شوفو! ما تكدر تهاجم تقنية تلغرام الرسمية!")
        return

    try:
        user_chat = bot.get_chat(user_id)
        if user_chat.type != "private":
            message.reply_text("هذا مو مستخدم!")
            return
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("ما أقدر ألكي هذا المستخدم.")
            return
        else:
            return

    if sql.is_user_gbanned(user_id):
        old_reason = sql.get_gbanned_user(user_id).reason
        if reason:
            if old_reason:
                message.reply_text(
                    "هذا المستخدم محظور عالمياً بالفعل للسبب التالي:\n"
                    "<code>{}</code>\n"
                    "تم تحديث السبب بسببك الجديد!".format(
                        html.escape(old_reason),
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                message.reply_text(
                    "هذا المستخدم محظور عالمياً بالفعل، بس ما كان عنده سبب؛ تم تحديثه!",
                )
        else:
            message.reply_text(
                "هذا المستخدم محظور عالمياً بالفعل؛ كنت راح أغير السبب بس ما عطيتني سبب...",
            )

        return

    message.reply_text("بعد شوية!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#حظر_عالمي\n"
        f"<b>المصدر:</b> <code>{chat_origin}</code>\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم المحظور:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>آيدي المحظور:</b> <code>{user_chat.id}</code>\n"
        f"<b>وقت الحدث:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>السبب:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>السبب:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nتعطّل التنسيق بسبب خطأ غير متوقع.",
            )

    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # تحقق من أن هذا القروب لم يعطّل الحظر العالمي
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"لا يمكن تنفيذ الحظر العالمي: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"ما أقدر أسوي حظر عالمي بسبب: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    send_to_list(
                        bot, DRAGONS + DEMONS, f"لا يمكن تنفيذ الحظر العالمي: {excp.message}",
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>القروبات المتأثرة:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(
            bot,
            DRAGONS + DEMONS,
            f"اكتمل الحظر العالمي! (تم حظر المستخدم في <code>{gbanned_chats}</code> قروب)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("تم! تم الحظر العالمي.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("تم! تم الحظر العالمي.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id,
            "#تنبيه\n"
            "تم تصنيفك كمستخدم ضار وتم حظرك من القروبات التي ندير.\n"
            f"<b>السبب:</b> <code>{html.escape(reason) if reason else 'لا يوجد'}</code>\n"
            f"<b>قروب الاستئناف:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # البوت محظور من قِبل المستخدم


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "لا يبدو أنك تشير إلى مستخدم أو أن الآيدي المحدد غير صحيح..",
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("هذا مو مستخدم!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("هذا المستخدم غير محظور عالمياً!")
        return

    message.reply_text(f"راح أعطي {user_chat.first_name} فرصة ثانية.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#رفع_حظر_عالمي\n"
        f"<b>المصدر:</b> <code>{chat_origin}</code>\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>آيدي المستخدم:</b> <code>{user_chat.id}</code>\n"
        f"<b>وقت الحدث:</b> <code>{current_time}</code>"
    )

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nتعطّل التنسيق بسبب خطأ غير متوقع.",
            )
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # تحقق من أن هذا القروب لم يعطّل الحظر العالمي
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"لا يمكن رفع الحظر العالمي: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"لا يمكن رفع الحظر العالمي: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    bot.send_message(
                        OWNER_ID, f"لا يمكن رفع الحظر العالمي: {excp.message}",
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>القروبات المتأثرة:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(bot, DRAGONS + DEMONS, "اكتمل رفع الحظر العالمي!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"تم رفع الحظر العالمي. استغرق {ungban_time} دقيقة")
    else:
        message.reply_text(f"تم رفع الحظر العالمي. استغرق {ungban_time} ثانية")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "ما اكو مستخدمين محظورين عالمياً! طيّبون أكثر مما توقعت...",
        )
        return

    banfile = "بعيداً عنهم.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"السبب: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="هاي قائمة المستخدمين المحظورين عالمياً.",
        )


def check_and_ban(update, user_id, should_message=True):

    if user_id in TIGERS or user_id in WOLVES:
        sw_ban = None
    else:
        sw_ban = sql.get_gbanned_user(user_id)

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            if sw_ban.reason:
                update.effective_message.reply_text(
                    f"<b>تنبيه الحظر العالمي</b>: هذا مستخدم محظور عالمياً.\n"
                    f"<b>السبب:</b> <code>{html.escape(sw_ban.reason)}</code>",
                    parse_mode=ParseMode.HTML,
                )
            else:
                update.effective_message.reply_text(
                    "<b>تنبيه الحظر العالمي</b>: هذا مستخدم محظور عالمياً.",
                    parse_mode=ParseMode.HTML,
                )


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # مراعاة: لا يتم تطبيق الحظر العالمي على المشرفين
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(
        context.bot.id,
    ).can_restrict_members:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                if not is_user_admin(chat, mem.id):
                    check_and_ban(update, mem.id)

        if msg.left_chat_member:
            pass


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0] in ("disable", "off"):
            sql.enable_gbans(update.effective_chat.id, False)
            update.effective_message.reply_text(
                "تم تعطيل الحظر العالمي في هذا القروب. لن يتم حظر المستخدمين المحظورين عالمياً.",
            )
        elif args[0] in ("enable", "on"):
            sql.enable_gbans(update.effective_chat.id, True)
            update.effective_message.reply_text(
                "تم تفعيل الحظر العالمي في هذا القروب. أي مستخدم محظور عالمياً سيتم حظره.",
            )
    else:
        update.effective_message.reply_text(
            "أعطيني بعض المعطيات لأعرف ماذا تريد! ('enable'/'disable' أو 'on'/'off')",
        )


def __stats__():
    return "× {} مستخدم محظور عالمياً.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "محظور عالمياً: <b>{}</b>"
    if is_gbanned:
        text = text.format("نعم")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\n<b>السبب:</b> {}".format(html.escape(user.reason))
    else:
        text = text.format("لا")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "هذا القروب يطبّق الحظر العالمي: `{}`.".format(
        sql.does_chat_gban(chat_id),
    )


__help__ = """
*للمشرفين فقط:*
 • `/gbanstat <on/off/enable/disable>`*:* تفعيل أو تعطيل تطبيق الحظر العالمي في هذا القروب.
"""

__mod_name__ = "الحظر العالمي"

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)
GBAN_STATUS = CommandHandler("gbanstat", gbanstat, filters=Filters.group)
GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)

__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]
