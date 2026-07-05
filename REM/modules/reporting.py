import html

from SaitamaRobot import LOGGER, DRAGONS, TIGERS, WOLVES, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin, user_not_admin
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import reporting_sql as sql
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = DRAGONS + TIGERS + WOLVES


@run_async
@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "تم تفعيل التبليغات! ستتلقى إشعاراً في كل مرة يُبلّغ فيها أحدهم عن شيء.",
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("تم إيقاف التبليغات! لن تتلقى أي تبليغات.")
        else:
            msg.reply_text(
                f"إعداد التبليغات الحالي: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "تم تفعيل التبليغات! سيتم إشعار المشرفين الذين فعّلوا التبليغات عند استخدام /report "
                    "أو @admin.",
                )

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "تم إيقاف التبليغات! لن يتم إشعار أي مشرف عند استخدام /report أو @admin.",
                )
        else:
            msg.reply_text(
                f"الإعداد الحالي لهذه المجموعة: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if not args:
            message.reply_text("أضف سبباً للتبليغ أولاً.")
            return ""

        if user.id == reported_user.id:
            message.reply_text("تبلّغ عن نفسك؟ هذا غريب...")
            return ""

        if user.id == bot.id:
            message.reply_text("محاولة ذكية.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("هل تبلّغ عن كارثة؟")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} بلّغ عن {mention_html(reported_user.id, reported_user.first_name)} للمشرفين!"

            msg = (
                f"<b>⚠️ تبليغ: </b>{html.escape(chat.title)}\n"
                f"<b> • بلّغ بواسطة:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • المُبلَّغ عنه:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • الرسالة المُبلَّغ عنها:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">انقر هنا</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "➡ رسالة",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⚠ طرد",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        "⛔️ حظر",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❎ حذف الرسالة",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = (
                f"{mention_html(user.id, user.first_name)} بلّغ عن "
                f"{mention_html(reported_user.id, reported_user.first_name)} للمشرفين!"
            )

            msg = f'{mention_html(user.id, user.first_name)} يطلب المشرفين في "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # لا يمكن إرسال رسائل للبوتات
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # إذا أعطى المستخدم سبباً، أرسل رسالته أيضاً
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:
                    LOGGER.exception("استثناء أثناء الإبلاغ عن مستخدم")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} أبلغ المشرفين عن هذه الرسالة.",
            parse_mode=ParseMode.HTML,
        )
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"هذه المجموعة مضبوطة لإرسال تبليغات المستخدمين للمشرفين عبر /report و @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        text = "ستتلقى التبليغات من المجموعات التي تكون مشرفاً فيها."
    else:
        text = "لن تتلقى *أي* تبليغات من المجموعات التي تكون مشرفاً فيها."
    return text


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ تم الطرد بنجاح")
            return ""
        except Exception as err:
            query.answer("🛑 فشل الطرد")
            bot.sendMessage(
                text=f"خطأ: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅ تم الحظر بنجاح")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"خطأ: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("🛑 فشل الحظر")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ تم حذف الرسالة")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"خطأ: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("🛑 فشل حذف الرسالة!")


__help__ = """
   • `/report <السبب>`*:* رد على رسالة لتبليغها للمشرفين.
   • `@admin`*:* رد على رسالة لتبليغها للمشرفين.
  *ملاحظة:* لا يعمل أي من هذين إذا استخدمهما المشرفون.

  *للمشرفين فقط:*
   • `/reports <on/off>`*:* تغيير إعداد التبليغ، أو عرض الحالة الحالية.
     • إذا نُفّذ بالخاص، يبدّل حالتك.
     • إذا نُفّذ بالقروب، يبدّل حالة ذلك القروب.
  """

SETTING_HANDLER = CommandHandler("reports", report_setting)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admin(s)?"), report)


REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "التبليغ"
__handlers__ = [
    (REPORT_HANDLER, REPORT_GROUP),
    (ADMIN_REPORT_HANDLER, REPORT_GROUP),
    (SETTING_HANDLER),
]
