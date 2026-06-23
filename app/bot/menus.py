from telegram import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💬 Chat", "👤 Profile"],
        ["📊 Usage", "⭐ Upgrade"],
        ["⚙ Settings", "❓ Help"]
    ],
    resize_keyboard=True
)
