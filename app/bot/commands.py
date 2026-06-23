from telegram import Update
from telegram.ext import ContextTypes

from app.bot.menus import MAIN_MENU
from app.services.profile_service import ProfileService
from app.services.usage_service import UsageLookupService

profile_service = ProfileService()
usage_service = UsageLookupService()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Welcome to ZyraXis AI\n\nYour AI workspace is ready.',
        reply_markup=MAIN_MENU
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start\n/help\n/profile\n/plans\n/stats\n/upgrade')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    profile = profile_service.get_profile(telegram_id)

    if not profile:
        await update.message.reply_text('Profile not found.')
        return

    plan = 'Premium' if profile['is_premium'] else 'Free'

    await update.message.reply_text(
        f'Plan: {plan}\nUser ID: {profile["telegram_id"]}\nJoined: {profile["created_at"]}'
    )

async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Free Plan\nPremium Plan\n\nUse /upgrade to purchase premium.')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    usage = usage_service.get_today(telegram_id)

    await update.message.reply_text(
        f'AI Requests: {usage["ai_requests"]}\nRoleplay: {usage["roleplay_requests"]}\nImages: {usage["image_requests"]}'
    )

async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Use /premium to upgrade with Telegram Stars.')
