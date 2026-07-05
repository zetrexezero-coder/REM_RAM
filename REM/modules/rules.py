from typing import Optional

import SaitamaRobot.modules.sql.rules_sql as sql
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.helper_funcs.string_handling import markdown_parser
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import escape_markdown


@run_async
def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# غير متزامن - ليس من معالج
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    reply_msg = update.message.reply_to_message
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "لم يتم ضبط اختصار القوانين لهذه المجموعة بشكل صحيح! اطلب من المشرفين إصلاح ذلك.\nربما نسوا الشرطة في المعرّف.",
            )
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"قوانين *{escape_markdown(chat.title)}* هي:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id, text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "لم يضع مشرفو المجموعة أي قوانين لهذه المحادثة بعد. "
            "لكن هذا لا يعني أنها فوضى...!",
        )
    elif rules and reply_msg:
        reply_msg.reply_text(
            "انقر على الزر أدناه لعرض القوانين.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="القوانين", url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    elif rules:
        update.effective_message.reply_text(
            "انقر على الزر أدناه لعرض القوانين.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="القوانين", url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    else:
        update.effective_message.reply_text(
            "لم يضع مشرفو المجموعة أي قوانين لهذه المحادثة بعد. "
            "لكن هذا لا يعني أنها فوضى...!",
        )


@run_async
@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # استخدام maxsplit لفصل الأمر عن المحتوى
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # ضبط الإزاحة الصحيحة
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset,
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("تم ضبط قوانين المجموعة بنجاح.")


@run_async
@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("تم حذف القوانين بنجاح!")


def __stats__():
    return f"• {sql.num_chats()} مجموعة لديها قوانين مضبوطة."


def __import_data__(chat_id, data):
    # ضبط قوانين المجموعة
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"هذه المجموعة لديها قوانين مضبوطة: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
   • `/rules`*:* عرض قوانين هذا القروب.

  *للمشرفين فقط:*
   • `/setrules <القوانين هنا>`*:* تعيين قوانين هذا القروب.
   • `/clearrules`*:* حذف قوانين هذا القروب.
  """

__mod_name__ = "القوانين"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
