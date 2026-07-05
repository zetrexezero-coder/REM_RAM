from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot import dispatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, Update
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext, Filters, CommandHandler

MARKDOWN_HELP = f"""
الماركداون أداة تنسيق قوية مدعومة من تلغرام. يوفر {dispatcher.bot.first_name} بعض التحسينات لضمان تحليل الرسائل المحفوظة بشكل صحيح، وللسماح لك بإنشاء أزرار.

• <code>_نص مائل_</code>: لف النص بـ '_' ينتج نصاً مائلاً
• <code>*نص عريض*</code>: لف النص بـ '*' ينتج نصاً عريضاً
• <code>`كود`</code>: لف النص بـ '`' ينتج نصاً بخط ثابت، يُعرف بـ 'كود'
• <code>[نص](رابط)</code>: ينشئ رابطاً - الرسالة ستظهر فقط <code>نص</code>، والضغط عليه سيفتح الصفحة على <code>رابط</code>.
<b>مثال:</b><code>[اختبار](example.com)</code>

• <code>[نص الزر](buttonurl:رابط)</code>: هذا تحسين خاص للسماح بإنشاء أزرار تلغرام في الماركداون. <code>نص الزر</code> هو ما سيظهر على الزر، و<code>رابط</code> هو الرابط الذي سيفتح.
<b>مثال:</b> <code>[هذا زر](buttonurl:example.com)</code>

إذا أردت أزرار متعددة على نفس السطر، استخدم :same هكذا:
<code>[واحد](buttonurl://example.com)
[اثنين](buttonurl://google.com:same)</code>
سينشئ هذا زرين على سطر واحد، بدلاً من زر لكل سطر.

تذكر أن رسالتك <b>يجب</b> أن تحتوي على نص غير الزر!
"""


@run_async
@user_admin
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True,
        )
    else:
        message.reply_text(
            args[1], quote=False, parse_mode="MARKDOWN", disable_web_page_preview=True,
        )
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "جرب تعيد توجيه الرسالة الجاية لي وراح تشوف! واستخدم #test",
    )
    update.effective_message.reply_text(
        "/save test هذا اختبار ماركداون. _مائل_, *عريض*, كود, "
        "[رابط](example.com) [زر](buttonurl:github.com) "
        "[زر2](buttonurl://google.com:same)",
    )


@run_async
def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            "راسلني بالخاص",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "مساعدة الماركداون",
                            url=f"t.me/{context.bot.username}?start=markdownhelp",
                        ),
                    ],
                ],
            ),
        )
        return
    markdown_help_sender(update)


__help__ = """
  *الأوامر المتوفرة:*
  *الماركداون:*
   • `/markdownhelp`*:* شرح سريع لكيفية عمل الماركداون في تلغرام - يمكن استخدامه فقط في الخاص
  *اللصق:*
   • `/paste`*:* حفظ المحتوى المردود عليه في `nekobin.com` والرد برابط
  *التفاعل:*
   • `/react`*:* يرد بتفاعل عشوائي
  *قاموس Urban:*
   • `/ud <كلمة>`*:* اكتب الكلمة أو التعبير الذي تريد البحث عنه
  *ويكيبيديا:*
   • `/wiki <استفسار>`*:* بحث في ويكيبيديا
  *خلفيات:*
   • `/wall <استفسار>`*:* الحصول على خلفية من wall.alphacoders.com
  *محول العملات:*
   • `/cash`*:* محول العملات
  مثال:
   `/cash 1 USD INR`
        _أو_
   `/cash 1 usd inr`
  النتيجة: `1.0 USD = 75.505 INR`
  *المناطق الزمنية:*
   • `/time <استفسار>`*:* يعرض معلومات عن منطقة زمنية.

  *الاستفسارات المتاحة:* رمز الدولة/اسم الدولة/اسم المنطقة الزمنية
  • 🕐 [قائمة المناطق الزمنية](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
  """

ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)

dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)

__mod_name__ = "إضافات"
__command_list__ = ["id", "echo"]
__handlers__ = [
    ECHO_HANDLER,
    MD_HELP_HANDLER,
]
