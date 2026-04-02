import os
from dotenv import load_dotenv

load_dotenv()


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


class Config(object):

    BOT_USERNAME = os.environ.get("BOT_USERNAME")
    API_ID = int(os.environ.get("API_ID"))

    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    ADMINS = (
        [int(i.strip()) for i in os.environ.get("ADMINS").split(",")]
        if os.environ.get("ADMINS")
        else []
    )
    DATABASE_NAME = os.environ.get("DATABASE_NAME", BOT_USERNAME)
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    OWNER_ID = int(os.environ.get("OWNER_ID", "7434248892"))  # id of the owner
    ADMINS.append(OWNER_ID) if OWNER_ID not in ADMINS else []

    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
    LIMIT = int(os.environ.get("LIMIT", "100"))
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "sdmoviepointes")
    BROADCAST_AS_COPY = is_enabled(
        (os.environ.get("BROADCAST_AS_COPY", "False")), False
    )
    WEB_SERVER = is_enabled(os.environ.get("WEB_SERVER", "False"), False)
    DATABASE_CHANNEL = (
        [int(i.strip()) for i in os.environ.get("DATABASE_CHANNEL").split(",")]
        if os.environ.get("DATABASE_CHANNEL")
        else []
    )
    USERNAME = os.environ.get("USERNAME", "")

    AUTO_DELETE = is_enabled(os.environ.get("AUTO_DELETE", "False"), False)
    AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "300"))

    SHORTENER_API = os.environ.get("SHORTENER_API")
    SHORTENER_SITE = os.environ.get("SHORTENER_SITE")

    FILE_HOW_TO_DOWNLOAD_LINK = os.environ.get("FILE_HOW_TO_DOWNLOAD_LINK")
    RESULTS_HOW_TO_DOWNLOAD_LINK = os.environ.get("RESULTS_HOW_TO_DOWNLOAD_LINK")
    REQUEST_MOVIE_URL = os.environ.get("REQUEST_MOVIE_URL")

    VALIDITY = [int(i.strip()) for i in os.environ.get("VALIDITY").split(",")] if os.environ.get("VALIDITY") else [999999999,]
    SESSION_STRING = os.environ.get("SESSION_STRING")

    TELEGRAPH_ACCESS_TOKEN = ['736edc901bb2b8b2787202f8519c4e652078784b316074fafbedfb26bc4d', '1fec664c2752da714492603b494b674e6b449829f27889ed46eb7144b11d', '5c09ffdb75ae522d166ee8679c4f0c44fa1664a1aeadb8697fa576604529', '4af0b3d57894a30c1b54194610569a412e1b5e508f216de40338b187843d', 'fecb697ba28fcfc1c14f758a756960ee62c1453c43440f419e3d5d24a98c', 'c8d9b088a0741b44c3b4a10f1923cd6e61c3bee8c628831db1d9ee890b62', '2d9d53e97172ec4512b2560e8123f1ec1212b81fc7b031ed04df96d0dbdd', '3c7afee76adc4f59091cf512c18c8b02160916bcdbf0d421f75d61ff39c4', '51291c987f8326f11c439cba714a08c8f61c49d5734052eccc209bd51901', '181e86d07630b24915f00801ebc79dfb0e15fa41c8daf63299ac068c60fd']
    
    TELEGRAM_JPEG = "https://www.trustedreviews.com/wp-content/uploads/sites/54/2018/01/Telegram-920x518.jpg"
    URL = os.environ.get("URL", "http://localhost:8080")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
    TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")


class Script(object):
    START_MESSAGE = os.environ.get("START_MESSAGE", "__I'm Find Your Movie Bot 🤖\nI Can Find Your Favourite Movies & Series In File Format.__")
    
    USER_HELP_MESSAGE = """/start - Used to start the bot.
/help - get help regarding the bot.
/about - get information about the bot.
/index - set a channel to index in a group.
/auto_delete - check the status of auto delete in a group.
/set_auto_delete - set the auto delete time in a group.
/request - request access from the bot owner.
/info - get information about a group.
/set_api - set the API in a group.
/api - get the API from a group.
/remove_api - remove the API from a group."""

    USER_HELP_MESSAGE = os.environ.get("USER_HELP_MESSAGE", USER_HELP_MESSAGE)
    
    ADMIN_HELP_MESSAGE = """/premium_groups - get the list of premium groups
/broadcast - broadcast message to users
/premium_reminder - remind users of premium groups of subscription
    """
    ADMIN_HELP_MESSAGE = os.environ.get("ADMIN_HELP_MESSAGE", ADMIN_HELP_MESSAGE)

    ABOUT_MESSAGE = os.environ.get("ABOUT_MESSAGE", "__Made With ❤️ By @sdmoviespointes __")

    AUTO_DELETE_TEXT = "This command is used to turn On/Off auto delete in your group.\nTo set auto delete time: /set_auto_delete\n\nUsage: `/auto_delete True/False`\nExample: /auto_delete True\n\nCurennt Config: {}"

    SET_AUTO_DELETE_TEXT = "This command is used to set auto delete time in your group.\nTo turn off auto delete: /auto_delete\n\nUsage: `/set_auto_delete seconds`\nExample: /set_auto_delete 300\n\nCurennt Config: {}"
    API_COMMAND_TEXT = "**Current API:** `{api}`\n**Current Webiste:** `{shortener_site}`\n\n**Set API:** /set_api\n**Remove API:** **  /remove_api"""
    NO_SUBSCRIPTION_TEXT = "Your group does not have any subscriptions, to get subscription /request"
    INDEX_TEXT = "This command is used to index your public channel from which bot will search movies\n\nUsage: `/index channel_id`\nExample: /index -100x\n\nCurennt Config: {}"

    NO_REPLY_TEXT = """No Results Found for **{}**❗️ 

**Type Only Movie Name 💬
Check Spelling On Google** 🔍"""

    GROUP_INFO_TEXT = """**Group ID:** `{group_id}`
**Group Link:** {group_link}
**Subscription Date:** `{subscription_date}`
**Expiry Date:** `{expiry_date}`
**Subscription Peroid Remaining:** `{time_remaining}`
**Shortener API Key:** `{shortener_api}`
**Shortener Domain:** `{shortener_site}`
**Auto Delete:** `{auto_delete}`
**Auto Delete Time:** `{auto_delete_time}`
**Indexed Channel:** `{index_channel}`"""

    SUBSCRIPTION_REMINDER_MESSAGE = """**Your subscription is gonna end soon. 
        
Renew your subscription to continue this service contact {owner}
Details:
"""

    RESULTS_MESSAGE = """Click Here 👇 For "{query}"

🍿🎬 [{query}]({url})
🍿🎬 [CLICK ME FOR RESULTS]({url})"""
