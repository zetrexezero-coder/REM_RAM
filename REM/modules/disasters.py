import html
import json
import os
from typing import Optional

from SaitamaRobot import (
    DEV_USERS,
    OWNER_ID,
    DRAGONS,
    SUPPORT_CHAT,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from SaitamaRobot.modules.helper_funcs.chat_status import (
    dev_plus,
    sudo_plus,
    whitelist_plus,
)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from SaitamaRobot.modules.log_channel import gloggable
from telegram import ParseMode, TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "SaitamaRobot/elevated_users.json")


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "هذا قروب مو مستخدم!"

    elif user_id == bot.id:
        reply = "هذا ما يشتغل بهالطريقة."

    else:
        reply = None
    return reply


@run_async
@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        message.reply_text("هذا العضو تنين بالفعل")
        return ""

    if user_id in DEMONS:
        rt += "تم طلب ترقية كارثة مستوى الشيطان إلى تنين."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        rt += "تم طلب ترقية كارثة مستوى الذئب إلى تنين."
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)

    data["sudos"].append(user_id)
    DRAGONS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt
        + "\nتم ضبط مستوى الكارثة للمستخدم {} إلى تنين!".format(
            user_member.first_name,
        ),
    )

    log_message = (
        f"#سودو\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addsupport(
    update: Update,
    context: CallbackContext,
) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "تم طلب تخفيض هذا التنين إلى شيطان"
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        message.reply_text("هذا المستخدم شيطان بالفعل.")
        return ""

    if user_id in WOLVES:
        rt += "تم طلب ترقية كارثة مستوى الذئب إلى شيطان"
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)

    data["supports"].append(user_id)
    DEMONS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nتم إضافة {user_member.first_name} كمستوى كارثة الشيطان!",
    )

    log_message = (
        f"#دعم\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "هذا المستخدم تنين، سيتم تخفيضه إلى ذئب."
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        rt += "هذا المستخدم شيطان بالفعل، سيتم تخفيضه إلى ذئب."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        message.reply_text("هذا المستخدم ذئب بالفعل.")
        return ""

    data["whitelists"].append(user_id)
    WOLVES.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nتم ترقية {user_member.first_name} إلى مستوى كارثة الذئب!",
    )

    log_message = (
        f"#قائمة_بيضاء\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addtiger(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "هذا المستخدم تنين، سيتم تخفيضه إلى نمر."
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        rt += "هذا المستخدم شيطان بالفعل، سيتم تخفيضه إلى نمر."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        rt += "هذا المستخدم ذئب بالفعل، سيتم تخفيضه إلى نمر."
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)

    if user_id in TIGERS:
        message.reply_text("هذا المستخدم نمر بالفعل.")
        return ""

    data["tigers"].append(user_id)
    TIGERS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nتم ترقية {user_member.first_name} إلى مستوى كارثة النمر!",
    )

    log_message = (
        f"#نمر\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        message.reply_text("تم طلب تخفيض هذا المستخدم إلى مدني")
        DRAGONS.remove(user_id)
        data["sudos"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#إلغاء_سودو\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = "<b>{}:</b>\n".format(html.escape(chat.title)) + log_message

        return log_message

    else:
        message.reply_text("هذا المستخدم ليس تنيناً!")
        return ""


@run_async
@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DEMONS:
        message.reply_text("تم طلب تخفيض هذا المستخدم إلى مدني")
        DEMONS.remove(user_id)
        data["supports"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#إلغاء_دعم\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("هذا المستخدم ليس شيطاناً!")
        return ""


@run_async
@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in WOLVES:
        message.reply_text("جارٍ التخفيض إلى مستخدم عادي")
        WOLVES.remove(user_id)
        data["whitelists"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#إلغاء_قائمة_بيضاء\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("هذا المستخدم ليس ذئباً!")
        return ""


@run_async
@sudo_plus
@gloggable
def removetiger(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, context)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in TIGERS:
        message.reply_text("جارٍ التخفيض إلى مستخدم عادي")
        TIGERS.remove(user_id)
        data["tigers"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#إلغاء_نمر\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>المستخدم:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("هذا المستخدم ليس نمراً!")
        return ""


@run_async
@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    reply = "<b>كوارث الذئاب المعروفون 🐺:</b>\n"
    m = update.effective_message.reply_text(
        "<code>جاري جمع المعلومات...</code>", parse_mode=ParseMode.HTML,
    )
    bot = context.bot
    for each_user in WOLVES:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    m.edit_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def tigerlist(update: Update, context: CallbackContext):
    reply = "<b>كوارث النمور المعروفون 🐯:</b>\n"
    m = update.effective_message.reply_text(
        "<code>جاري جمع المعلومات...</code>", parse_mode=ParseMode.HTML,
    )
    bot = context.bot
    for each_user in TIGERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    m.edit_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    m = update.effective_message.reply_text(
        "<code>جاري جمع المعلومات...</code>", parse_mode=ParseMode.HTML,
    )
    reply = "<b>كوارث الشياطين المعروفون 👹:</b>\n"
    for each_user in DEMONS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    m.edit_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    m = update.effective_message.reply_text(
        "<code>جاري جمع المعلومات...</code>", parse_mode=ParseMode.HTML,
    )
    true_sudo = list(set(DRAGONS) - set(DEV_USERS))
    reply = "<b>كوارث التنانين المعروفون 🐉:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    m.edit_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    m = update.effective_message.reply_text(
        "<code>جاري جمع المعلومات...</code>", parse_mode=ParseMode.HTML,
    )
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "<b>أعضاء رابطة الأبطال ⚡️:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    m.edit_text(reply, parse_mode=ParseMode.HTML)


__help__ = """
  *⚠️ تنبيه:*
  الأوامر المذكورة هنا تعمل فقط للمستخدمين ذوي الصلاحية الخاصة وتُستخدم أساساً لحل المشاكل والتصحيح.
  مشرفو ومالكو القروبات لا يحتاجون هذه الأوامر.

   ╔ *عرض جميع المستخدمين ذوي الصلاحية الخاصة:*
   ╠ `/dragons`*:* عرض جميع كوارث التنانين
   ╠ `/demons`*:* عرض جميع كوارث المشعوذين
   ╠ `/tigers`*:* عرض جميع كوارث النمور
   ╠ `/wolves`*:* عرض جميع كوارث الذئاب
   ╠ `/heroes`*:* عرض جميع أعضاء رابطة الأبطال
   ╠ `/adddragon`*:* إضافة مستخدم لفئة التنانين
   ╠ `/adddemon`*:* إضافة مستخدم لفئة المشعوذين
   ╠ `/addtiger`*:* إضافة مستخدم لفئة النمور
   ╠ `/addwolf`*:* إضافة مستخدم لفئة الذئاب
   ╚ إضافة مطور غير موجود، على المطورين معرفة كيفية إضافة أنفسهم

   ╔ *البينغ:*
   ╠ `/ping`*:* الحصول على زمن استجابة البوت لسيرفرات تلغرام
   ╚ `/pingall`*:* الحصول على جميع أزمنة الاستجابة المسجلة

   ╔ *البث: (لصاحب البوت فقط)*
   ╠  *ملاحظة:* يدعم الماركداون الأساسي
   ╠ `/broadcastall`*:* بث في كل مكان
   ╠ `/broadcastusers`*:* بث لجميع المستخدمين
   ╚ `/broadcastgroups`*:* بث لجميع القروبات

   ╔ *معلومات القروبات:*
   ╠ `/groups`*:* عرض القروبات مع الاسم والآيدي وعدد الأعضاء كملف نصي
   ╠ `/leave <الآيدي>`*:* مغادرة القروب، يجب أن يحتوي الآيدي على شرطة
   ╠ `/stats`*:* عرض إحصائيات البوت العامة
   ╠ `/getchats`*:* الحصول على قائمة أسماء القروبات التي شوهد المستخدم فيها. لصاحب البوت فقط
   ╚ `/ginfo username/link/ID`*:* عرض لوحة معلومات كاملة عن القروب

   ╔ *التحكم بالوصول:*
   ╠ `/ignore`*:* حظر مستخدم من
   ╠  استخدام البوت بشكل كامل
   ╠ `/lockdown <off/on>`*:* تبديل إمكانية إضافة البوت للقروبات
   ╠ `/notice`*:* إزالة مستخدم من قائمة الحظر
   ╚ `/ignoredlist`*:* عرض المستخدمين المحظورين

   ╔ *الحظر العام:*
   ╠ `/gban المستخدم السبب`*:* حظر مستخدم عالمياً
   ╚ `/ungban المستخدم السبب`*:* رفع الحظر العام عن المستخدم

  """

SUDO_HANDLER = CommandHandler(("addsudo", "adddragon"), addsudo)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport)
TIGER_HANDLER = CommandHandler(("addtiger"), addtiger)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addwolf"), addwhitelist)
UNSUDO_HANDLER = CommandHandler(("removesudo", "removedragon"), removesudo)
UNSUPPORT_HANDLER = CommandHandler(("removesupport", "removedemon"), removesupport)
UNTIGER_HANDLER = CommandHandler(("removetiger"), removetiger)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist", "removewolf"), removewhitelist)

WHITELISTLIST_HANDLER = CommandHandler(["whitelistlist", "wolves"], whitelistlist)
TIGERLIST_HANDLER = CommandHandler(["tigers"], tigerlist)
SUPPORTLIST_HANDLER = CommandHandler(["supportlist", "demons"], supportlist)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "dragons"], sudolist)
DEVLIST_HANDLER = CommandHandler(["devlist", "heroes"], devlist)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(TIGER_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNTIGER_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(TIGERLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "الكوارث"
__handlers__ = [
    SUDO_HANDLER,
    SUPPORT_HANDLER,
    TIGER_HANDLER,
    WHITELIST_HANDLER,
    UNSUDO_HANDLER,
    UNSUPPORT_HANDLER,
    UNTIGER_HANDLER,
    UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER,
    TIGERLIST_HANDLER,
    SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER,
    DEVLIST_HANDLER,
]
