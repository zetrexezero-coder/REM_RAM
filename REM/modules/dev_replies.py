"""
ميزة الردود المخصصة للمطور
============================
يقدر المطور (OWNER_ID + DEV_USERS) يضيف ردود تلقائية:
  • أي عضو يكتب الكلمة المحددة → البوت يرد تلقائياً بالرسالة المحفوظة

الأوامر (للمطور فقط):
  /addreply <الكلمة> | <الرد>      ← يضيف رد جديد
  /delreply <الكلمة>               ← يحذف رد
  /listreplies                     ← يعرض كل الردود
  /clearreplies                    ← يحذف كل الردود (للمالك فقط)
"""

import json
import os
import re

from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, run_async

from SaitamaRobot import dispatcher, OWNER_ID, DEV_USERS

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ملف تخزين الردود
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_REPLIES_FILE = os.path.join(os.path.dirname(__file__), "..", "dev_replies.json")

HANDLER_GROUP = 12   # أولوية أعلى من الفلاتر العادية


def _load() -> dict:
    """يحمّل الردود من الملف."""
    if not os.path.exists(_REPLIES_FILE):
        return {}
    try:
        with open(_REPLIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    """يحفظ الردود في الملف."""
    with open(_REPLIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _is_dev(user_id: int) -> bool:
    """يتحقق إذا المستخدم من المطورين."""
    return user_id == OWNER_ID or user_id in DEV_USERS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# أوامر الإدارة (للمطور فقط)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@run_async
def add_dev_reply(update: Update, context: CallbackContext):
    """
    /addreply <الكلمة> | <الرد>
    يضيف رداً تلقائياً لكلمة/جملة محددة.
    """
    message = update.effective_message
    user    = update.effective_user

    if not _is_dev(user.id):
        message.reply_text("🚫 هذا الأمر للمطور فقط.")
        return

    # بنية الأمر: /addreply كلمة | رد
    full_text = message.text.partition(" ")[2].strip()  # كل شيء بعد /addreply
    if "|" not in full_text:
        message.reply_text(
            "❌ الصيغة الصحيحة:\n"
            "<code>/addreply الكلمة | الرد هنا</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    trigger, _, reply_text = full_text.partition("|")
    trigger    = trigger.strip().lower()
    reply_text = reply_text.strip()

    if not trigger or not reply_text:
        message.reply_text("❌ اكتب الكلمة والرد، ما يجيز يكون أحدهم فاضي.")
        return

    data = _load()
    data[trigger] = reply_text
    _save(data)

    message.reply_text(
        f"✅ <b>تم الحفظ!</b>\n"
        f"<b>الكلمة:</b> <code>{trigger}</code>\n"
        f"<b>الرد:</b> {reply_text}",
        parse_mode=ParseMode.HTML,
    )


@run_async
def del_dev_reply(update: Update, context: CallbackContext):
    """
    /delreply <الكلمة>
    يحذف رداً محفوظاً.
    """
    message = update.effective_message
    user    = update.effective_user

    if not _is_dev(user.id):
        message.reply_text("🚫 هذا الأمر للمطور فقط.")
        return

    trigger = message.text.partition(" ")[2].strip().lower()
    if not trigger:
        message.reply_text("❌ اكتب الكلمة اللي تبي تحذف ردها.")
        return

    data = _load()
    if trigger not in data:
        message.reply_text(f"🤷 ما فيه رد محفوظ للكلمة: <code>{trigger}</code>", parse_mode=ParseMode.HTML)
        return

    del data[trigger]
    _save(data)
    message.reply_text(f"✅ تم حذف الرد للكلمة: <code>{trigger}</code>", parse_mode=ParseMode.HTML)


@run_async
def list_dev_replies(update: Update, context: CallbackContext):
    """
    /listreplies
    يعرض كل الردود المحفوظة.
    """
    message = update.effective_message
    user    = update.effective_user

    if not _is_dev(user.id):
        message.reply_text("🚫 هذا الأمر للمطور فقط.")
        return

    data = _load()
    if not data:
        message.reply_text("📭 ما فيه ردود محفوظة حتى الآن.")
        return

    lines = ["<b>📋 الردود المحفوظة:</b>\n"]
    for i, (trigger, reply) in enumerate(data.items(), 1):
        preview = reply[:40] + "..." if len(reply) > 40 else reply
        lines.append(f"{i}. <code>{trigger}</code> ← {preview}")

    message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@run_async
def clear_dev_replies(update: Update, context: CallbackContext):
    """
    /clearreplies
    يحذف كل الردود (للمالك فقط).
    """
    message = update.effective_message
    user    = update.effective_user

    if user.id != OWNER_ID:
        message.reply_text("🚫 هذا الأمر للمالك فقط.")
        return

    _save({})
    message.reply_text("🗑️ تم مسح كل الردود المحفوظة.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الاستجابة التلقائية لأي رسالة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@run_async
def auto_reply_handler(update: Update, context: CallbackContext):
    """
    يراقب كل الرسائل ويرد إذا تطابقت مع كلمة محفوظة.
    • يتجاهل رسائل البوتات (لمنع حلقات الرد)
    • يتجاهل إذا الرد يحتوي على trigger نفسه (ضد الحلقات)
    • رد واحد فقط للرسالة الواحدة
    """
    message = update.effective_message
    if not message or not message.text:
        return

    # تجاهل رسائل البوتات الأخرى لمنع حلقات الرد
    sender = update.effective_user
    if sender and sender.is_bot:
        return

    text = message.text.lower().strip()
    data = _load()

    if not data:
        return

    # نفحص كل trigger: إذا الرسالة تحتوي عليه كـ كلمة كاملة
    for trigger, reply_text in data.items():
        pattern = r"(^|[\s\W])" + re.escape(trigger) + r"($|[\s\W])"
        if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
            # منع حلقة: لا ترد إذا الرد يحتوي على نفس الـ trigger
            if re.search(pattern, reply_text.lower(), re.IGNORECASE | re.UNICODE):
                return
            message.reply_text(reply_text)
            return   # رد واحد فقط للرسالة الواحدة


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التسجيل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADDREPLY_H   = CommandHandler("addreply",    add_dev_reply)
DELREPLY_H   = CommandHandler("delreply",    del_dev_reply)
LISTREPLIES_H= CommandHandler("listreplies", list_dev_replies)
CLEARREPLIES_H=CommandHandler("clearreplies",clear_dev_replies)
AUTO_REPLY_H = MessageHandler(
    Filters.text & ~Filters.update.edited_message & ~Filters.command,
    auto_reply_handler,
)

dispatcher.add_handler(ADDREPLY_H)
dispatcher.add_handler(DELREPLY_H)
dispatcher.add_handler(LISTREPLIES_H)
dispatcher.add_handler(CLEARREPLIES_H)
dispatcher.add_handler(AUTO_REPLY_H, HANDLER_GROUP)

__mod_name__ = "ردود المطور"
__help__ = """
*ردود المطور التلقائية* ─ للمطور فقط:

   • `/addreply <الكلمة> | <الرد>`*:* يضيف رداً تلقائياً
     مثال: `/addreply أهلاً | وعليكم السلام 👋`
   • `/delreply <الكلمة>`*:* يحذف الرد المحفوظ للكلمة
   • `/listreplies`*:* يعرض كل الردود المحفوظة
   • `/clearreplies`*:* يمسح كل الردود (للمالك فقط)

*كيف تشتغل:*
   أي شخص يكتب الكلمة المحفوظة في أي رسالة → البوت يرد عليها تلقائياً.
"""
__handlers__ = [ADDREPLY_H, DELREPLY_H, LISTREPLIES_H, CLEARREPLIES_H, (AUTO_REPLY_H, HANDLER_GROUP)]
