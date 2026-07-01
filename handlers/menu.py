from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('💬 Chat with AI', callback_data='chat_ai'), InlineKeyboardButton('🎭 Roleplay', callback_data='roleplay')],
        [InlineKeyboardButton('📄 Analyze File', callback_data='analyze_file'), InlineKeyboardButton('🖼 Generate Image', callback_data='generate_image')],
        [InlineKeyboardButton('🎥 Generate Video PRO', callback_data='generate_video'), InlineKeyboardButton('🔍 Web Search', callback_data='web_search')],
        [InlineKeyboardButton('📊 Usage', callback_data='usage'), InlineKeyboardButton('👑 Premium', callback_data='premium')],
        [InlineKeyboardButton('⚙ Settings', callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🟣 ZyraXis AI Menu', reply_markup=reply_markup)