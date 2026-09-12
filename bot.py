import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")

WELCOME = """مرحبًا بك في SaQR Agency 🦅

اختر الخدمة التي تريدها من القائمة بالأسفل:"""

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 خدمات السوشيال ميديا", callback_data="social")],
        [InlineKeyboardButton("💻 اشتراكات البرامج", callback_data="subscriptions")],
        [InlineKeyboardButton("🎨 التصميم والجرافيك", callback_data="design")],
        [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "social":
        text = """📱 خدمات السوشيال ميديا

• متابعين
• لايكات
• مشاهدات
• ريتش وتفاعل

للطلب أو معرفة الأسعار تواصل مع الدعم."""
    elif query.data == "subscriptions":
        text = """💻 اشتراكات البرامج

• اشتراكات برامج التصميم
• أدوات الذكاء الاصطناعي
• خدمات رقمية متنوعة

للطلب أو معرفة الأسعار تواصل مع الدعم."""
    elif query.data == "design":
        text = """🎨 التصميم والجرافيك

• تصميم بوستات
• هويات بصرية
• إعلانات
• تصميمات سوشيال ميديا

للطلب تواصل مع الدعم."""
    else:
        text = """📞 الدعم

اكتب لنا الخدمة التي تريدها وسنساعدك في إتمام الطلب."""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])
    await query.edit_message_text(text, reply_markup=keyboard)

async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(WELCOME, reply_markup=main_menu())

def run():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(home_handler, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("SaQR Agency bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run()
