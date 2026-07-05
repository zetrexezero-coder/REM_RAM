import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from SaitamaRobot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
    can_delete,
)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user_and_text
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.log_channel import gloggable, loggable


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أن هذا مستخدم.")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("لا يمكنني إيجاد هذا الشخص.")
        return log_message
    if user_id == bot.id:
        message.reply_text("هل تريد حظر نفسي؟ لن أفعل ذلك!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("تحاول وضعي في مواجهة كارثة من مستوى الإله؟")
        elif user_id in DEV_USERS:
            message.reply_text("لا أستطيع التصرف ضد أحد من فريقنا.")
        elif user_id in DRAGONS:
            message.reply_text(
                "محاربة هذا التنين هنا ستعرّض المدنيين للخطر.",
            )
        elif user_id in DEMONS:
            message.reply_text(
                "احضر أمراً من جمعية الأبطال لمحاربة كارثة من مستوى الشيطان.",
            )
        elif user_id in TIGERS:
            message.reply_text(
                "احضر أمراً من جمعية الأبطال لمحاربة كارثة من مستوى النمر.",
            )
        elif user_id in WOLVES:
            message.reply_text("قدرات الذئب تجعله محصّناً من الحظر!")
        else:
            message.reply_text("هذا المستخدم محصّن ولا يمكن حظره.")
        return log_message
    if message.text.startswith("/s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'حظر_صامت' if silent else 'حظر'}\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>السبب:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()
            return log

        reply = (
            f"<code>❕</code><b>حدث حظر</b>\n"
            f"<code> </code><b>•  المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  السبب:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML, quote=False)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            if silent:
                return log
            message.reply_text("تم الحظر!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "خطأ في حظر المستخدم %s في المجموعة %s (%s) بسبب %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("حدث خطأ ما...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أن هذا مستخدم.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("لا يمكنني إيجاد هذا المستخدم.")
        return log_message
    if user_id == bot.id:
        message.reply_text("لن أحظر نفسي، هل أنت جاد؟")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("لا أرغب في ذلك.")
        return log_message

    if not reason:
        message.reply_text("لم تحدد مدة الحظر!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#حظر_مؤقت\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>المدة:</b> {time_val}"
    )
    if reason:
        log += "\n<b>السبب:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.sendMessage(
            chat.id,
            f"تم الحظر! سيتم حظر المستخدم {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"لمدة {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            message.reply_text(
                f"تم الحظر! سيتم حظر المستخدم لمدة {time_val}.", quote=False,
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "خطأ في حظر المستخدم %s في المجموعة %s (%s) بسبب %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("لا يمكنني حظر هذا المستخدم.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أن هذا مستخدم.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("لا يمكنني إيجاد هذا المستخدم.")
        return log_message
    if user_id == bot.id:
        message.reply_text("لن أفعل ذلك.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("أتمنى لو كان بإمكاني طرد هذا المستخدم....")
        return log_message

    res = chat.unban_member(user_id)
    if res:
        bot.sendMessage(
            chat.id,
            f"تمت الضربة! {mention_html(member.user.id, html.escape(member.user.first_name))}.",
            parse_mode=ParseMode.HTML,
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#طرد\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>السبب:</b> {reason}"

        return log

    else:
        message.reply_text("لا يمكنني طرد هذا المستخدم.")

    return log_message


@run_async
@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("أتمنى لو كان بإمكاني... لكنك مشرف.")
        return

    res = update.effective_chat.unban_member(user_id)
    if res:
        update.effective_message.reply_text("*تم طردك من المجموعة*")
    else:
        update.effective_message.reply_text("لا أستطيع :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أن هذا مستخدم.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("لا يمكنني إيجاد هذا المستخدم.")
        return log_message
    if user_id == bot.id:
        message.reply_text("كيف سأرفع حظري عن نفسي وأنا لست هنا؟")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("أليس هذا الشخص هنا بالفعل؟")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("تم رفع الحظر، يمكن للمستخدم الانضمام الآن!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#رفع_الحظر\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>السبب:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS or user.id not in TIGERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("أعطني معرّف مجموعة صحيح.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا يمكنني إيجاد هذا المستخدم.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("أنت بالفعل في المجموعة!")
        return

    chat.unban_member(user.id)
    message.reply_text("تم رفع حظرك.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """

   • `/punchme`*:* يضرب المستخدم الذي أصدر الأمر

  *للمشرفين فقط:*
   • `/ban <المستخدم>`*:* حظر مستخدم. (عبر اسم المستخدم، أو الرد)
   • `/sban <المستخدم>`*:* حظر صامت لمستخدم. يحذف الأمر والرسالة المردود عليها ولا يرد. (عبر اسم المستخدم، أو الرد)
   • `/tban <المستخدم> x(m/h/d)`*:* حظر مستخدم لمدة `x`. (عبر اسم المستخدم، أو الرد). `m` = `دقائق`، `h` = `ساعات`، `d` = `أيام`.
   • `/unban <المستخدم>`*:* رفع الحظر عن مستخدم. (عبر اسم المستخدم، أو الرد)
   • `/punch <المستخدم>`*:* طرد مستخدم من القروب بضربة، (عبر اسم المستخدم، أو الرد)
  """

BAN_HANDLER = CommandHandler(["ban", "sban"], ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
PUNCH_HANDLER = CommandHandler("punch", punch)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
PUNCHME_HANDLER = DisableAbleCommandHandler("punchme", punchme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(PUNCHME_HANDLER)

__mod_name__ = "الطرد والحظر"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    PUNCH_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    PUNCHME_HANDLER,
]
