import html
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot import dispatcher, DRAGONS
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from telegram.ext import CallbackContext, run_async, CallbackQueryHandler
import SaitamaRobot.modules.sql.approve_sql as sql
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.log_channel import loggable
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest


@loggable
@user_admin
@run_async
def approve(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "مو عارف منو تقصد، لازم تحدد المستخدم!",
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            "هذا المستخدم مشرف أصلاً - الأقفال والقوائم السوداء ومكافحة الإسبام ما تنطبق عليه.",
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) معتمد بالفعل في {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"تم اعتماد [{member.user['first_name']}](tg://user?id={member.user['id']}) في {chat_title}! ما راح تنطبق عليه الأقفال والقوائم السوداء ومكافحة الإسبام.",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#اعتماد\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@loggable
@user_admin
@run_async
def disapprove(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "مو عارف منو تقصد، لازم تحدد المستخدم!",
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text("هذا المستخدم مشرف، ما أقدر ألغي اعتماده.")
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} مو معتمد بعد!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"{member.user['first_name']} ما عاد معتمداً في {chat_title}.",
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#إلغاء_اعتماد\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@user_admin
@run_async
def approved(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "هاي المستخدمين المعتمدين.\n"
    approved_users = sql.list_approved(message.chat_id)
    for i in approved_users:
        member = chat.get_member(int(i.user_id))
        msg += f"- `{i.user_id}`: {member.user['first_name']}\n"
    if msg.endswith("المعتمدين.\n"):
        message.reply_text(f"ما اكو مستخدمين معتمدين في {chat_title}.")
        return ""
    else:
        message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@user_admin
@run_async
def approval(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text(
            "مو عارف منو تقصد، لازم تحدد المستخدم!",
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"{member.user['first_name']} مستخدم معتمد. الأقفال ومكافحة الإسبام والقوائم السوداء ما تنطبق عليه.",
        )
    else:
        message.reply_text(
            f"{member.user['first_name']} مو مستخدم معتمد. تنطبق عليه الأوامر العادية.",
        )


@run_async
def unapproveall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "بس مالك القروب يكدر يلغي اعتماد كل المستخدمين دفعة وحدة.",
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="إلغاء الموافقة عن جميع المستخدمين", callback_data="unapproveall_user",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="إلغاء", callback_data="unapproveall_cancel",
                    ),
                ],
            ],
        )
        update.effective_message.reply_text(
            f"أكيد تريد إلغاء اعتماد كل المستخدمين في {chat.title}؟ هذا الإجراء ما يرجع!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@run_async
def unapproveall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            approved_users = sql.list_approved(chat.id)
            users = [int(i.user_id) for i in approved_users]
            for user_id in users:
                sql.disapprove(chat.id, user_id)      
            message.edit_text("تم إلغاء اعتماد كل المستخدمين بالقروب.")
            return

        if member.status == "administrator":
            query.answer("بس مالك القروب يكدر يسوي هذا.")

        if member.status == "member":
            query.answer("لازم تكون مشرف تسوي هذا.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            message.edit_text("تم إلغاء حذف كل المستخدمين المعتمدين.")
            return ""
        if member.status == "administrator":
            query.answer("بس مالك القروب يكدر يسوي هذا.")
        if member.status == "member":
            query.answer("لازم تكون مشرف تسوي هذا.")


__help__ = """

  أحياناً، قد تثق بمستخدم بأنه لن يرسل محتوى غير مرغوب فيه.
  قد لا تكون ثقتك كافية لترقيته كمشرف، لكن قد تكون مستعداً لاستثنائه من الأقفال والكلمات المحظورة ومكافحة الإسبام.

  هذا هو الغرض من الموافقات - وافق على المستخدمين الموثوقين لتسمح لهم بالإرسال

  *أوامر المشرفين:*
  - `/approval`*:* التحقق من حالة موافقة مستخدم في هذا القروب.
  - `/approve`*:* الموافقة على مستخدم. لن تنطبق عليه الأقفال والكلمات المحظورة ومكافحة الإسبام بعد الآن.
  - `/unapprove`*:* إلغاء الموافقة عن مستخدم. سيخضع مجدداً للأقفال والكلمات المحظورة ومكافحة الإسبام.
  - `/approved`*:* عرض قائمة كل المستخدمين الموافَق عليهم.
  - `/unapproveall`*:* إلغاء الموافقة عن *كل* المستخدمين في القروب. لا يمكن التراجع عن هذا.
  """

APPROVE = DisableAbleCommandHandler("approve", approve)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove)
APPROVED = DisableAbleCommandHandler("approved", approved)
APPROVAL = DisableAbleCommandHandler("approval", approval)
UNAPPROVEALL = DisableAbleCommandHandler("unapproveall", unapproveall)
UNAPPROVEALL_BTN = CallbackQueryHandler(unapproveall_btn, pattern=r"unapproveall_.*")

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "الموافقات"
__command_list__ = ["approve", "unapprove", "approved", "approval"]
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
