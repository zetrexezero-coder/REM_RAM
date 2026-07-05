"""
وحدة "المطور وريم"
==================
• عندما أي شخص يكتب "المطور" → يرد البوت بصورة ريم
• عندما أي شخص يكتب "ريم" → يرد البوت بكلام عشوائي ويتفاعل معه

لتفعيل صورة ريم:
  1. ضع صورة باسم reem_photo.jpg في مجلد SaitamaRobot/
     ─ أو ─
  2. اعيّن REEM_PHOTO_ID في السطر التالي بعد إرسال الصورة للبوت
"""

import os
import random

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async

from SaitamaRobot import dispatcher

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# إعداد صورة ريم
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REEM_PHOTO_ID   = None  # ← ضع file_id الصورة هنا (اختياري)
REEM_PHOTO_FILE = os.path.join(os.path.dirname(__file__), "..", "reem_photo.jpg")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ردود ريم العشوائية (يتغيرون في كل مرة)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REEM_RANDOM_REPLIES = [
    "نعم؟ 🌹 ايش تبي؟",
    "مرحبا بيك! كيف حالك اليوم؟ 😊",
    "أنا هنا يا عزيزي، ايش تحتاج؟ 💕",
    "ذكرتني؟ ❤️",
    "هلا هلا! شو الأخبار؟",
    "ريم قالت مرحبا 🌸",
    "يسعد مساك/صباحك 🌺",
    "آهلين فيك! كيف يومك؟ 🌼",
    "ويييين كنت؟ وحشتني! 💛",
    "هاي! شو تبي من ريم اليوم؟ 😄",
    "لبيك! ايش أقدر أساعدك؟ 🌷",
    "أهلاً وسهلاً! ريم حاضرة 😉",
    "اشتقت ليّ؟ ريم هنا! 🌹",
    "صح لساني! كيف أنت/ي؟ 🤗",
    "ريم دايماً تحب تسمع صوتك 💫",
    "مرحبتين! ايش الجديد؟ ✨",
    "هاهه، ذكرتني؟ 😏",
    "أهلاً يا غالي/ة! 🌸",
    "ريم بالخدمة ❤️‍🔥",
    "شو عندك يا حبيبي/ة؟ 😊",
    "يعني منتبه/ة عليّ؟ 🥰",
    "ها! ايش ودك؟ 😁",
]

# ردود إضافية تعتمد على الوقت/السياق
REEM_QUESTION_REPLIES = [
    "قولي قولي! أنا أسمع 👂",
    "أيووو؟ ايش تقول؟ 😄",
    "أكمل! ريم مهتمة 😊",
    "هلا! ايش بالك؟ 💭",
]

REEM_MORNING_REPLIES = [
    "صباح الورد يا قلبي! 🌹☀️",
    "صباح النور! ريم صاحية وجاهزة 😊",
    "صبحت وأول شي تذكرني؟ كيوت! ☕🌸",
]

REEM_NIGHT_REPLIES = [
    "مسا الخير يا قمر! 🌙",
    "مساك نور! ريم هنا حتى آخر الليل 🌃",
    "مسا الورد! كيف كان يومك؟ 🌙🌹",
]


def _get_reem_reply(message_text: str) -> str:
    """يختار رد عشوائي مناسب."""
    text_lower = message_text.lower()

    # كلمات الصباح
    if any(w in text_lower for w in ["صباح", "صبحت", "صبح الخير", "good morning"]):
        return random.choice(REEM_MORNING_REPLIES)

    # كلمات المساء
    if any(w in text_lower for w in ["مساء", "مسا", "مسا الخير", "good evening", "good night"]):
        return random.choice(REEM_NIGHT_REPLIES)

    # أسئلة
    if "؟" in message_text or "?" in message_text:
        return random.choice(REEM_QUESTION_REPLIES)

    # الرد الافتراضي العشوائي
    return random.choice(REEM_RANDOM_REPLIES)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# هاندلر "المطور" → صورة ريم
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def almutatwer_reply(update: Update, context: CallbackContext):
    """يرد بصورة ريم عند ذكر 'المطور'."""
    message = update.effective_message

    if REEM_PHOTO_ID:
        message.reply_photo(
            photo=REEM_PHOTO_ID,
            caption="ريم 🌹 — المطوّرة",
        )
    elif os.path.exists(REEM_PHOTO_FILE):
        with open(REEM_PHOTO_FILE, "rb") as photo:
            message.reply_photo(
                photo=photo,
                caption="ريم 🌹 — المطوّرة",
            )
    else:
        message.reply_text(
            "🌹 <b>ريم</b> هي المطوّرة!\n"
            "( الصورة لم تُضبط بعد — أضف reem_photo.jpg للمجلد )",
            parse_mode=ParseMode.HTML,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# هاندلر "ريم" → تفاعل عشوائي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@run_async
def reem_chat_reply(update: Update, context: CallbackContext):
    """
    يرد بكلام عشوائي عند ذكر كلمة 'ريم' في الرسالة.
    يدعم: ريم، ريووم، ريمة، reem
    """
    message = update.effective_message
    text = message.text or ""

    reply = _get_reem_reply(text)
    message.reply_text(reply)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التسجيل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# تفعيل في المجموعات والخاص معاً
_any_text = Filters.text & ~Filters.update.edited_message

ALMUTATWER_HANDLER = MessageHandler(
    _any_text & Filters.regex(r"المطور"),
    almutatwer_reply,
)

REEM_CHAT_HANDLER = MessageHandler(
    _any_text & Filters.regex(r"(ريم|ريوم|ريووم|ريمة|reem)\b"),
    reem_chat_reply,
)

dispatcher.add_handler(ALMUTATWER_HANDLER)
dispatcher.add_handler(REEM_CHAT_HANDLER)

__mod_name__ = "المطور وريم"
__handlers__ = [ALMUTATWER_HANDLER, REEM_CHAT_HANDLER]
