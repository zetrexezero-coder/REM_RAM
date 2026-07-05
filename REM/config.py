import json
import os


def get_user_list(config, key):
    with open("{}/SaitamaRobot/{}".format(os.getcwd(), config), "r") as json_file:
        return json.load(json_file)[key]


class Config(object):
    LOGGER = True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # تُقرأ من متغيرات Railway تلقائياً
    # أضفها في: Railway → Variables
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    API_ID       = int(os.environ.get("API_ID", 36318666))
    API_HASH     = os.environ.get("API_HASH", "328dd2d7f3ba09913454e402b3687453")
    TOKEN        = os.environ.get("TOKEN", "8955102989:AAFnYJkTGm5l1DJ-Go7WUwvdqenaWbrhkOk")
    OWNER_ID     = int(os.environ.get("OWNER_ID", 2088738010))
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "RE_M_RAM")
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "")
    JOIN_LOGGER  = int(os.environ.get("JOIN_LOGGER", 0))
    EVENT_LOGS   = int(os.environ.get("EVENT_LOGS", 0))

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")

    SPAMWATCH_API          = os.environ.get("SPAMWATCH_API", "")
    SPAMWATCH_SUPPORT_CHAT = "@SpamWatchSupport"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # أزرار /start — غيّرها هنا مباشرة
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    BTN_UPDATES   = os.environ.get("BTN_UPDATES",   "https://t.me/REM_7BOT")
    BTN_HOWTO     = os.environ.get("BTN_HOWTO",     "https://t.me/REM_5BOT")
    BTN_SOURCE    = os.environ.get("BTN_SOURCE",    "https://t.me/REM_5BOT/3")
    BTN_EXTRA     = os.environ.get("BTN_EXTRA",     "https://t.me/REM_8BOT")
    BTN_EXTRA_TXT = os.environ.get("BTN_EXTRA_TXT", "القناة الاحتياطيه")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # المستخدمون المميزون
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    DRAGONS   = get_user_list("elevated_users.json", "sudos")
    DEV_USERS = get_user_list("elevated_users.json", "devs")
    DEMONS    = get_user_list("elevated_users.json", "supports")
    TIGERS    = get_user_list("elevated_users.json", "tigers")
    WOLVES    = get_user_list("elevated_users.json", "whitelists")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # إعدادات ثابتة
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    LOAD         = []
    NO_LOAD      = ["rss", "cleaner", "connection", "math",
                    "translation", "sibylsystem", "anime",
                    "remote_cmds", "speed_test"]
    WEBHOOK      = False
    INFOPIC      = True
    URL          = None
    PORT         = int(os.environ.get("PORT", 5000))
    WORKERS      = 8
    DEL_CMDS     = True
    STRICT_GBAN  = True
    ALLOW_EXCL   = True
    BAN_STICKER  = "CAADAgADOwADPPEcAXkko5EB3YGYAg"
    DONATION_LINK= os.environ.get("DONATION_LINK", "")
    CASH_API_KEY = os.environ.get("CASH_API_KEY", "")
    TIME_API_KEY = os.environ.get("TIME_API_KEY", "")
    WALL_API     = os.environ.get("WALL_API", "")
    AI_API_KEY   = os.environ.get("AI_API_KEY", "")
    BL_CHATS     = []
    CERT_PATH    = None
    SPAMMERS     = None
    ALLOW_CHATS  = True


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
