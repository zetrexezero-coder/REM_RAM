import random
import html
from datetime import datetime
import humanize

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from SaitamaRobot.modules.sql import afk_sql as sql
from SaitamaRobot.modules.users import get_user_id
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


@run_async
def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user:  # تجاهل القنوات
        return

    if user.id in [777000, 1087968824]:
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nتم اختصار سبب غيابك إلى 100 حرف."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text(
            "{} غير متواجد الآن!{}".format(fname, notice),
        )
    except BadRequest:
        pass


@run_async
def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.effective_message

    if not user:  # تجاهل القنوات
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # لا ترد على رسالة الانضمام
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} موجود الآن!",
                "{} عاد!",
                "{} في المجموعة الآن!",
                "{} استيقظ!",
                "{} عاد للاتصال!",
                "{} عاد أخيراً!",
                "أهلاً بعودتك {}!",
                "أين {}؟\nفي المجموعة!",
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(
                chosen_option.format(firstname),
            )
        except:
            return


@run_async
def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION],
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION],
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = get_user_id(
                message.text[ent.offset: ent.offset + ent.length],
            )
            if not user_id:
                # لا ينبغي أن يحدث هذا، لأن المستخدم يجب أن يكون قد تحدث مسبقاً. ربما تغيّر اسم المستخدم؟
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = bot.get_chat(user_id)
            except BadRequest:
                print("خطأ: لا يمكن جلب المستخدم {} لوحدة AFK".format(user_id))
                return
            fst_name = chat.first_name

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update: Update, context: CallbackContext, user_id: int, fst_name: str, userc_id: int):
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)

        if int(userc_id) == int(user_id):
            return

        time = humanize.naturaldelta(datetime.now() - user.time)

        if not user.reason:
            res = "{} غير متواجد.\n\nآخر ظهور منذ {}.".format(
                fst_name,
                time,
            )
            update.effective_message.reply_text(res)
        else:
            res = "{} غير متواجد.\nالسبب: <code>{}</code>\n\nآخر ظهور منذ {}.".format(
                html.escape(fst_name),
                html.escape(user.reason),
                time,
            )
            update.effective_message.reply_text(res, parse_mode="html")


__help__ = """
   • `/afk <السبب>`*:* وضع نفسك كغير متواجد (AFK).
   • `brb <السبب>`*:* نفس أمر afk - لكنه ليس أمراً رسمياً.
  عند وضعك كغير متواجد، أي إشارة (منشن) لك سيتم الرد عليها برسالة تفيد بأنك غير متاح!
  """

AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"(?i)^brb(.*)$"), afk, friendly="afk",
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "غير متواجد (AFK)"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
