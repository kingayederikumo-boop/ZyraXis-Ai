"""
Command router for the Telegram worker.

Two kinds of commands:
- Canned (COMMANDS): reply is computed here directly, no AI call needed.
- Orchestrated (ORCHESTRATED_COMMANDS): needs a real AI call + quota check,
  so this module only validates args; the worker hands off to the
  Orchestrator for the actual work.

Every handler shares the same signature (telegram_id, first_name, args) so
dispatch() can call any of them uniformly - a previous version of this file
had inconsistent signatures per handler, which would have thrown TypeError
depending on which command ran. Caught before it shipped.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import Config
from app.database.session import SessionLocal
from app.gateway.auth import AuthService

auth = AuthService()


from app.gateway.guard import Gatekeeper

gate = Gatekeeper()


def _bar(pct: int) -> str:
    filled = min(10, max(0, pct // 10))
    return "█" * filled + "░" * (10 - filled)


def cmd_start(telegram_id: str, first_name: str = None, args: str = ""):
    auth.get_or_create_user(telegram_id)
    name = f" {first_name}" if first_name else ""
    return f"👋 Hey{name}! I'm ZyraXis AI.\n\nHow can I assist you today?", None


def cmd_help(telegram_id: str, first_name: str = None, args: str = ""):
    text = (
        "*ZyraXis AI — Commands*\n\n"
        "/chat — AI chat mode\n"
        "/roleplay — Enter roleplay mode\n"
        "/exitroleplay — Leave roleplay mode\n"
        "/analyze — How to analyze a file (just send one)\n"
        "/image <description> — Generate an image\n"
        "/video <description> — Generate a video\n"
        "/search <question> — Web search\n"
        "/code <request> — Coding assistant\n"
        "/usage — View today's usage\n"
        "/premium — View subscription plans\n"
        "/menu — Open the main menu\n"
    )
    return text, None


def cmd_menu(telegram_id: str, first_name: str = None, args: str = ""):
    keyboard = [
        [InlineKeyboardButton("💬 Chat with AI", callback_data="menu:chat"),
         InlineKeyboardButton("🎭 Roleplay", callback_data="menu:roleplay")],
        [InlineKeyboardButton("📄 Analyze File", callback_data="menu:file"),
         InlineKeyboardButton("🖼 Generate Image", callback_data="menu:image")],
        [InlineKeyboardButton("🎥 Generate Video", callback_data="menu:video"),
         InlineKeyboardButton("🔍 Web Search", callback_data="menu:search")],
        [InlineKeyboardButton("📊 Usage", callback_data="menu:usage"),
         InlineKeyboardButton("👑 Premium", callback_data="menu:premium")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings")],
    ]
    return "Main Menu", InlineKeyboardMarkup(keyboard)


def cmd_usage(telegram_id: str, first_name: str = None, args: str = ""):
    user = auth.get_or_create_user(telegram_id)
    tier = user.tier

    remaining = gate.remaining(int(telegram_id), tier, "chat")
    limit = gate._limit(tier, "chat")
    used = limit - remaining
    ai_pct = int(used / limit * 100) if limit else 0

    text = (
        f"*Today's Usage* ({tier.upper()})\n\n"
        f"AI Chat\n{_bar(ai_pct)} {min(100, ai_pct)}%\n\n"
        f"Use /premium to see what upgrading unlocks."
    )
    return text, None


def cmd_premium(telegram_id: str, first_name: str = None, args: str = ""):
    text = (
        "*ZyraXis Premium*\n\n"
        "*Pro* — 200 ⭐\n"
        "Better reasoning, better web search, video generation, faster responses.\n\n"
        "*Expert* — 1100 ⭐\n"
        "Coding Assistant, Advanced Reasoning, Research Mode, "
        "highest limits, priority execution."
    )
    keyboard = [
        [InlineKeyboardButton("Upgrade to Pro — 200⭐", callback_data="upgrade:pro")],
        [InlineKeyboardButton("Upgrade to Expert — 1100⭐", callback_data="upgrade:expert")],
    ]
    return text, InlineKeyboardMarkup(keyboard)


def cmd_chat(telegram_id: str, first_name: str = None, args: str = ""):
    auth.set_mode(telegram_id, "chat")
    return "You're in AI chat mode. Just send me a message!", None


def cmd_roleplay(telegram_id: str, first_name: str = None, args: str = ""):
    auth.set_mode(telegram_id, "roleplay")
    text = (
        "🎭 Roleplay mode on.\n\n"
        "Describe a character or scenario and I'll stay in character. "
        "Use /exitroleplay to leave."
    )
    return text, None


def cmd_exit_roleplay(telegram_id: str, first_name: str = None, args: str = ""):
    auth.set_mode(telegram_id, "chat")
    return "Back to normal chat.", None


def cmd_admin(telegram_id: str, first_name: str = None, args: str = ""):
    if not auth.is_admin(telegram_id):
        return "Not authorized.", None

    db = SessionLocal()
    try:
        total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        by_tier = db.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier").fetchall()
    finally:
        db.close()

    tier_lines = "\n".join(f"  {tier}: {count}" for tier, count in by_tier)
    return f"*Admin*\n\nTotal users: {total}\n{tier_lines}", None


def cmd_premium_add(telegram_id: str, first_name: str = None, args: str = ""):
    """Manual tier grant. This is the practical stopgap for paid tiers
    until the real Stars payment flow exists - not a placeholder, this is
    genuinely how you'd support a user who paid you outside the bot for now."""
    if not auth.is_admin(telegram_id):
        return "Not authorized.", None

    parts = args.strip().split()
    if len(parts) != 2 or parts[1] not in Config.VALID_TIERS:
        return "Usage: /premiumadd <telegram_id> <free|pro|expert>", None

    target_id, tier = parts
    auth.get_or_create_user(target_id)
    auth.set_tier(target_id, tier)
    return f"Set {target_id} to {tier}.", None


def cmd_premium_remove(telegram_id: str, first_name: str = None, args: str = ""):
    if not auth.is_admin(telegram_id):
        return "Not authorized.", None

    target_id = args.strip()
    if not target_id:
        return "Usage: /premiumremove <telegram_id>", None

    auth.get_or_create_user(target_id)
    auth.set_tier(target_id, "free")
    return f"Set {target_id} to free.", None


def cmd_image_check(telegram_id: str, first_name: str = None, args: str = ""):
    """Validates only - real generation runs through the Orchestrator."""
    if not args.strip():
        return "Usage: /image a description of what you want to see", None
    return None  # None = valid, hand off to orchestrator as feature=image


def cmd_search_check(telegram_id: str, first_name: str = None, args: str = ""):
    if not args.strip():
        return "Usage: /search your question", None
    return None


def cmd_code_check(telegram_id: str, first_name: str = None, args: str = ""):
    if not args.strip():
        return "Usage: /code what you want help with", None
    return None


def cmd_video_check(telegram_id: str, first_name: str = None, args: str = ""):
    if not args.strip():
        return "Usage: /video a description of the video you want", None
    return None


def cmd_analyze(telegram_id: str, first_name: str = None, args: str = ""):
    """No standalone action - analysis is triggered by uploading a document
    (see process_document in the worker). This just tells the user how."""
    return (
        "Send me a file (PDF, DOCX, TXT, CSV, JSON, or code) and I'll "
        "analyze it. Add a caption with your question if you have one - "
        "otherwise I'll summarize it."
    ), None


def cmd_image_prompt(telegram_id: str, first_name: str = None, args: str = ""):
    return "Send /image followed by a description, e.g. /image a cat astronaut on the moon", None


def cmd_video_prompt(telegram_id: str, first_name: str = None, args: str = ""):
    return "Send /video followed by a description, e.g. /video a golden retriever running on a beach", None


def cmd_search_prompt(telegram_id: str, first_name: str = None, args: str = ""):
    return "Send /search followed by your question, e.g. /search latest news on the Mars rover", None


COMMANDS = {
    "/start": cmd_start,
    "/help": cmd_help,
    "/menu": cmd_menu,
    "/usage": cmd_usage,
    "/premium": cmd_premium,
    "/chat": cmd_chat,
    "/roleplay": cmd_roleplay,
    "/exitroleplay": cmd_exit_roleplay,
    "/analyze": cmd_analyze,
    "/admin": cmd_admin,
    "/premiumadd": cmd_premium_add,
    "/premiumremove": cmd_premium_remove,
}

# Needs a real AI call + quota check. Maps command -> (feature, validator).
ORCHESTRATED_COMMANDS = {
    "/image": ("image", cmd_image_check),
    "/search": ("search", cmd_search_check),
    "/code": ("code", cmd_code_check),
    "/video": ("video", cmd_video_check),
}

# Menu buttons carry no argument text (the user just tapped, didn't type),
# so these can't hand off to the Orchestrator directly - they either set a
# mode (chat/roleplay) or tell the user how to invoke the real command.
# menu:settings has nothing built behind it yet, deliberately unmapped.
CALLBACK_COMMANDS = {
    "menu:usage": cmd_usage,
    "menu:premium": cmd_premium,
    "menu:chat": cmd_chat,
    "menu:roleplay": cmd_roleplay,
    "menu:file": cmd_analyze,
    "menu:image": cmd_image_prompt,
    "menu:video": cmd_video_prompt,
    "menu:search": cmd_search_prompt,
}


def dispatch(text: str, telegram_id: str, first_name: str = None):
    """Returns one of:
    - ("canned", reply_text, reply_markup): a direct reply, send as-is
    - ("orchestrate", feature, args): hand off to the Orchestrator
    - ("invalid", error_text): a known orchestrated command with bad/missing args
    - None: not a recognized command at all
    """
    parts = text.strip().split(maxsplit=1)
    command = parts[0].split("@")[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command in COMMANDS:
        reply_text, reply_markup = COMMANDS[command](telegram_id, first_name=first_name, args=args)
        return ("canned", reply_text, reply_markup)

    if command in ORCHESTRATED_COMMANDS:
        feature, validator = ORCHESTRATED_COMMANDS[command]
        result = validator(telegram_id, first_name=first_name, args=args)
        if result is not None:
            error_text, _ = result
            return ("invalid", error_text)
        return ("orchestrate", feature, args)

    return None
