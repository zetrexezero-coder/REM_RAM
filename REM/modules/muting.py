import html
from typing import Optional

from SaitamaRobot import LOGGER, TIGERS, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    user_admin,
)
from SaitamaRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.log_channel import loggable
from telegram import Bot, Chat, ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = "لا يبدو أنك تشير إلى مستخدم أو أن الآيدي المحدد غير صحيح.."
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            reply = "لا يمكنني إيجاد هذا المستخدم"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "لن أُسكت نفسي!"
        return reply

    if is_user_admin(chat, user_id, member) or user_id in TIGERS:
        reply = "لا يمكنني إسكات هذا الشخص."
        return reply

    return None


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#إسكات\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>السبب:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        bot.sendMessage(
            chat.id,
            f"تم إسكات <b>{html.escape(member.user.first_name)}</b> إلى أجل غير مسمى!",
            parse_mode=ParseMode.HTML,
        )
        return log

    else:
        message.reply_text("هذا المستخدم مُسكَت بالفعل!")

    return ""


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "يجب أن تعطيني اسم مستخدم أو ترد على شخص لرفع الإسكات عنه.",
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("هذا المستخدم لديه حق الكلام بالفعل.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass
            bot.sendMessage(
                chat.id,
                f"تم رفع الإسكات عن <b>{html.escape(member.user.first_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#رفع_إسكات\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        message.reply_text(
            "هذا المستخدم ليس في المجموعة أصلاً، رفع الإسكات عنه لن يجعله يتحدث!",
        )

    return ""


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text("لم تحدد مدة الإسكات!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#إسكات_مؤقت\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>المدة:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>السبب:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime,
            )
            bot.sendMessage(
                chat.id,
                f"تم إسكات <b>{html.escape(member.user.first_name)}</b> لمدة {time_val}!",
                parse_mode=ParseMode.HTML,
            )
            return log
        else:
            message.reply_text("هذا المستخدم مُسكَت بالفعل.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            message.reply_text(f"تم الإسكات لمدة {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "خطأ في إسكات المستخدم %s في المجموعة %s (%s) بسبب %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("لا يمكنني إسكات هذا المستخدم.")

    return ""


__help__ = """
  *للمشرفين فقط:*
   • `/mute <المستخدم>`*:* إسكات مستخدم. يمكن استخدامه كرد أيضاً، لإسكات المستخدم المردود عليه.
   • `/tmute <المستخدم> x(m/h/d)`*:* إسكات مستخدم لمدة x. (عبر اسم المستخدم، أو الرد). `m` = `دقائق`، `h` = `ساعات`، `d` = `أيام`.
   • `/unmute <المستخدم>`*:* رفع الإسكات عن مستخدم. يمكن استخدامه كرد أيضاً.
  """

MUTE_HANDLER = CommandHandler("mute", mute)
UNMUTE_HANDLER = CommandHandler("unmute", unmute)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "الإسكات"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
