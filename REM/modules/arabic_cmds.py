"""
الأوامر العربية بدون / ─ تشتغل كل أوامر البوت بالكلام العادي
==============================================================
كيفية الاستخدام:
  • رد على رسالة + اكتب الأمر  ➜  طرد، حظر، اسكت، فك الحظر...
  • أو اكتب الأمر + المنشن/الآيدي  ➜  طرد @username
"""

import html
import re
from telegram import ParseMode, Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async
from telegram.utils.helpers import mention_html

from SaitamaRobot import dispatcher, DRAGONS
from SaitamaRobot.modules.helper_funcs.chat_status import is_user_admin, is_user_ban_protected
from SaitamaRobot.modules.helper_funcs.extraction import extract_user_and_text

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الكلمات العربية لكل أمر (تدعم أشكال متعددة)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KICK_PATTERN   = re.compile(r"^(طرد|اطرد|طردوه|طرده|طرديه)\b", re.IGNORECASE)
BAN_PATTERN    = re.compile(r"^(حظر|احظر|تحظير|باند|بان)\b", re.IGNORECASE)
UNBAN_PATTERN  = re.compile(r"^(فك\s*الحظر|رفع\s*الحظر|ارفع\s*الحظر|فك\s*البان|انباند)\b", re.IGNORECASE)
MUTE_PATTERN   = re.compile(r"^(اسكت|إسكات|كتم|اكتم|سكته|سكتها)\b", re.IGNORECASE)
UNMUTE_PATTERN = re.compile(r"^(فك\s*الكتم|رفع\s*الكتم|ارفع\s*الكتم|فك\s*الإسكات|رفع\s*الإسكات)\b", re.IGNORECASE)
PROMOTE_PATTERN= re.compile(r"^(ترقية|رقّه|رقيه|رقّيه|اعطه\s*ادمن|ادمن)\b", re.IGNORECASE)
DEMOTE_PATTERN = re.compile(r"^(تنزيل|نزّله|نزله|شيل\s*الادمن|خفّض|خفضه)\b", re.IGNORECASE)
WARN_PATTERN        = re.compile(r"^(حذّره|حذره|انذره|إنذار|تحذير)\b", re.IGNORECASE)
RESETWARN_PATTERN   = re.compile(r"^(مسح\s*التحذيرات|امسح\s*التحذيرات|صفّر\s*التحذيرات)\b", re.IGNORECASE)
PIN_PATTERN         = re.compile(r"^(ثبّت|تثبيت|ثبت)\b", re.IGNORECASE)
UNPIN_PATTERN  = re.compile(r"^(الغِ\s*التثبيت|الغ\s*التثبيت|رفع\s*التثبيت)\b", re.IGNORECASE)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دالة مساعدة: استخراج المستخدم المستهدف من الرسالة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _get_target(message, context):
    """
    يرجع (user_id, reason)
    يقرأ من: الرد على رسالة ← المنشن ← الآيدي الرقمي
    """
    # احذف الكلمة الأولى (الأمر) وخذ الباقي كـ args
    parts = message.text.split(None, 1)
    raw_args = parts[1].split() if len(parts) > 1 else []
    return extract_user_and_text(message, raw_args)


def _check_admin(chat, user_id):
    """يرجع True إذا المستخدم مشرف أو في قائمة التنانين"""
    return is_user_admin(chat, user_id) or user_id in DRAGONS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الطرد (Kick) - بدون حظر
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_kick(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, reason = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي تطرده أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أطرد نفسي 😄")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم في القروب.")
        return

    if is_user_ban_protected(chat, user_id, member) and user.id not in DRAGONS:
        message.reply_text("هذا المستخدم محمي ما أقدر أطرده.")
        return

    try:
        chat.kick_member(user_id)
        chat.unban_member(user_id)  # يطرده بدون حظر نهائي
        reply = (
            f"👢 <b>تم الطرد!</b>\n"
            f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            reply += f"\n<b>السبب:</b> {html.escape(reason)}"
        message.reply_text(reply, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        message.reply_text(f"ما قدرت أطرده: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الحظر (Ban)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_ban(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, reason = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي تحظره أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أحظر نفسي 😄")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    if is_user_ban_protected(chat, user_id, member) and user.id not in DRAGONS:
        message.reply_text("هذا المستخدم محمي ما أقدر أحظره.")
        return

    try:
        chat.kick_member(user_id)
        reply = (
            f"🔨 <b>تم الحظر!</b>\n"
            f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            reply += f"\n<b>السبب:</b> {html.escape(reason)}"
        message.reply_text(reply, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        message.reply_text(f"ما قدرت أحظره: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# رفع الحظر (Unban)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_unban(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, _ = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي ترفع حظره أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("أنا مو محظور 😅")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("✅ تم رفع الحظر.")
    except BadRequest as e:
        message.reply_text(f"ما قدرت أرفع الحظر: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الإسكات (Mute)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_mute(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, reason = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي تسكّته أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أسكّت نفسي!")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    if is_user_admin(chat, user_id) and user.id not in DRAGONS:
        message.reply_text("ما أقدر أسكّت مشرف.")
        return

    try:
        bot.restrict_chat_member(chat.id, user_id, ChatPermissions(can_send_messages=False))
        reply = (
            f"🔇 <b>تم الإسكات!</b>\n"
            f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            reply += f"\n<b>السبب:</b> {html.escape(reason)}"
        message.reply_text(reply, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        message.reply_text(f"ما قدرت أسكّته: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# رفع الإسكات (Unmute)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_unmute(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, _ = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي ترفع إسكاته أو ذكر اسمه.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    try:
        bot.restrict_chat_member(
            chat.id, user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
                can_send_polls=True,
                can_change_info=True,
                can_pin_messages=True,
            ),
        )
        message.reply_text(
            f"🔊 تم رفع الإسكات عن {mention_html(member.user.id, member.user.first_name)}!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        message.reply_text(f"ما قدرت أرفع الإسكات: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الترقية (Promote)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_promote(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    promoter = chat.get_member(user.id)
    if not (getattr(promoter, "can_promote_members", False) or promoter.status == "creator") and user.id not in DRAGONS:
        message.reply_text("ما عندك صلاحية ترقية أعضاء.")
        return

    user_id, _ = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على العضو اللي تبي ترقيه أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أرقّي نفسي!")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    if member.status in ("administrator", "creator"):
        message.reply_text("هذا المستخدم مشرف أصلاً.")
        return

    bot_member = chat.get_member(bot.id)
    try:
        bot.promote_chat_member(
            chat.id, user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
        message.reply_text(
            f"⬆️ تمت ترقية {mention_html(member.user.id, member.user.first_name)} بنجاح!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        message.reply_text(f"ما قدرت أرقّيه: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التنزيل (Demote)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_demote(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    # التحقق من صلاحية ترقية/تنزيل الأعضاء
    caller = chat.get_member(user.id)
    if caller.status != "creator" and not caller.can_promote_members and user.id not in DRAGONS:
        message.reply_text("ما عندك صلاحية تنزيل الأعضاء.")
        return

    user_id, _ = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المشرف اللي تبي تنزّله أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أنزّل نفسي!")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    if member.status == "creator":
        message.reply_text("ما أقدر أنزّل منشئ القروب.")
        return

    try:
        bot.promote_chat_member(
            chat.id, user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
        )
        message.reply_text(
            f"⬇️ تم تنزيل {mention_html(member.user.id, member.user.first_name)} من الإدارة.",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        message.reply_text(f"ما قدرت أنزّله: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التثبيت (Pin)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_pin(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    # التحقق من صلاحية تثبيت الرسائل
    caller = chat.get_member(user.id)
    if caller.status != "creator" and not getattr(caller, "can_pin_messages", False) and user.id not in DRAGONS:
        message.reply_text("ما عندك صلاحية تثبيت الرسائل.")
        return

    if not message.reply_to_message:
        message.reply_text("رد على الرسالة اللي تبي تثبّتها.")
        return

    try:
        bot.pin_chat_message(chat.id, message.reply_to_message.message_id, disable_notification=False)
        message.reply_text("📌 تم تثبيت الرسالة.")
    except BadRequest as e:
        message.reply_text(f"ما قدرت أثبّت الرسالة: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# إلغاء التثبيت (Unpin)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_unpin(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    # التحقق من صلاحية التثبيت
    caller = chat.get_member(user.id)
    if caller.status != "creator" and not getattr(caller, "can_pin_messages", False) and user.id not in DRAGONS:
        message.reply_text("ما عندك صلاحية إلغاء التثبيت.")
        return

    try:
        bot.unpin_chat_message(chat.id)
        message.reply_text("📌 تم إلغاء التثبيت.")
    except BadRequest as e:
        message.reply_text(f"ما قدرت أرفع التثبيت: {e.message}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التحذير (Warn)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_warn(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user
    bot     = context.bot

    if not _check_admin(chat, user.id):
        return

    user_id, reason = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي تحذّره أو ذكر اسمه.")
        return

    if user_id == bot.id:
        message.reply_text("ما أقدر أحذّر نفسي!")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    if is_user_admin(chat, user_id) and user.id not in DRAGONS:
        message.reply_text("ما أقدر أحذّر مشرف.")
        return

    # استدعاء وظيفة التحذير الأصلية عبر أمر /warn
    context.args = [str(user_id)]
    if reason:
        context.args.append(reason)

    # إرسال أمر /warn مباشرة للوظيفة
    try:
        from SaitamaRobot.modules.warns import warn_user as _warn_user
        _warn_user(update, context)
    except Exception:
        # fallback إذا ما اشتغل الاستيراد
        message.reply_text(
            f"⚠️ تم إرسال تحذير لـ {mention_html(member.user.id, member.user.first_name)}!"
            + (f"\n<b>السبب:</b> {html.escape(reason)}" if reason else ""),
            parse_mode=ParseMode.HTML,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# مسح التحذيرات (Reset Warns)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def ar_resetwarn(update: Update, context: CallbackContext):
    message = update.effective_message
    chat    = update.effective_chat
    user    = update.effective_user

    if not _check_admin(chat, user.id):
        return

    user_id, _ = _get_target(message, context)
    if not user_id:
        message.reply_text("🤔 رد على المستخدم اللي تبي تمسح تحذيراته أو ذكر اسمه.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        message.reply_text("ما لقيت هذا المستخدم.")
        return

    context.args = [str(user_id)]
    try:
        from SaitamaRobot.modules.warns import reset_warns as _reset_warns
        _reset_warns(update, context)
    except Exception:
        message.reply_text(
            f"✅ تم مسح تحذيرات {mention_html(member.user.id, member.user.first_name)}!",
            parse_mode=ParseMode.HTML,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# تسجيل الهاندلرز
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_group_text = Filters.text & Filters.group & ~Filters.update.edited_message

AR_KICK_H      = MessageHandler(_group_text & Filters.regex(KICK_PATTERN),      ar_kick)
AR_BAN_H       = MessageHandler(_group_text & Filters.regex(BAN_PATTERN),       ar_ban)
AR_UNBAN_H     = MessageHandler(_group_text & Filters.regex(UNBAN_PATTERN),     ar_unban)
AR_MUTE_H      = MessageHandler(_group_text & Filters.regex(MUTE_PATTERN),      ar_mute)
AR_UNMUTE_H    = MessageHandler(_group_text & Filters.regex(UNMUTE_PATTERN),    ar_unmute)
AR_PROM_H      = MessageHandler(_group_text & Filters.regex(PROMOTE_PATTERN),   ar_promote)
AR_DEM_H       = MessageHandler(_group_text & Filters.regex(DEMOTE_PATTERN),    ar_demote)
AR_PIN_H       = MessageHandler(_group_text & Filters.regex(PIN_PATTERN),       ar_pin)
AR_UNPIN_H     = MessageHandler(_group_text & Filters.regex(UNPIN_PATTERN),     ar_unpin)
AR_WARN_H      = MessageHandler(_group_text & Filters.regex(WARN_PATTERN),      ar_warn)
AR_RESETWARN_H = MessageHandler(_group_text & Filters.regex(RESETWARN_PATTERN), ar_resetwarn)

for h in [AR_KICK_H, AR_BAN_H, AR_UNBAN_H, AR_MUTE_H, AR_UNMUTE_H,
          AR_PROM_H, AR_DEM_H, AR_PIN_H, AR_UNPIN_H,
          AR_WARN_H, AR_RESETWARN_H]:
    dispatcher.add_handler(h)

__mod_name__ = "الأوامر العربية"
__help__ = """
*الأوامر العربية بدون /* ─ تشتغل بالكلام العادي في القروب:

  *للمشرفين (رد على رسالة أو اذكر اسم المستخدم):*
   • `طرد` ─ يطرد العضو بدون حظر
   • `حظر` ─ يحظر العضو نهائياً
   • `فك الحظر` ─ يرفع الحظر
   • `اسكت` ─ يسكّت العضو
   • `فك الكتم` ─ يرفع الإسكات
   • `حذّره` ─ يعطي تحذير للعضو
   • `مسح التحذيرات` ─ يمسح كل تحذيرات العضو
   • `ترقية` ─ يرقّي العضو لمشرف
   • `تنزيل` ─ يرفع صلاحيات المشرف
   • `ثبّت` ─ يثبّت الرسالة (رد عليها)
   • `الغِ التثبيت` ─ يلغي التثبيت
"""
__handlers__ = [AR_KICK_H, AR_BAN_H, AR_UNBAN_H, AR_MUTE_H, AR_UNMUTE_H,
                AR_PROM_H, AR_DEM_H, AR_PIN_H, AR_UNPIN_H,
                AR_WARN_H, AR_RESETWARN_H]
