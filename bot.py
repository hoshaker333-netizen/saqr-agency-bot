import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")


WELCOME = """🦅 مرحبًا بك في SaQR Agency

اختر الخدمة التي تريدها من القائمة بالأسفل:"""


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 خدمات السوشيال ميديا", callback_data="social")],
        [InlineKeyboardButton("💻 اشتراكات البرامج", callback_data="subscriptions")],
        [InlineKeyboardButton("🎨 التصميم والجرافيك", callback_data="design")],
        [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="support")],
    ])


def social_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram")],
        [InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok")],
        [InlineKeyboardButton("▶️ YouTube", callback_data="platform_youtube")],
        [InlineKeyboardButton("📘 Facebook", callback_data="platform_facebook")],
        [InlineKeyboardButton("💬 Telegram", callback_data="platform_telegram")],
        [InlineKeyboardButton("🟢 WhatsApp", callback_data="platform_whatsapp")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


def platform_menu(platform):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 متابعين", callback_data=f"service_{platform}_followers")],
        [InlineKeyboardButton("❤️ لايكات", callback_data=f"service_{platform}_likes")],
        [InlineKeyboardButton("👀 مشاهدات", callback_data=f"service_{platform}_views")],
        [InlineKeyboardButton("🔥 ريتش وتفاعل", callback_data=f"service_{platform}_engagement")],
        [InlineKeyboardButton("🔙 المنصات", callback_data="social")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME,
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "social":
        await query.edit_message_text(
            "📱 خدمات السوشيال ميديا\n\nاختر المنصة:",
            reply_markup=social_menu()
        )
        return

    platforms = {
        "instagram": "📸 Instagram",
        "tiktok": "🎵 TikTok",
        "youtube": "▶️ YouTube",
        "facebook": "📘 Facebook",
        "telegram": "💬 Telegram",
        "whatsapp": "🟢 WhatsApp",
    }

    if query.data.startswith("platform_"):
        platform = query.data.replace("platform_", "")
        name = platforms.get(platform, platform)

        await query.edit_message_text(
            f"{name}\n\nاختر الخدمة التي تريدها:",
            reply_markup=platform_menu(platform)
        )
        return

    if query.data.startswith("service_"):
        parts = query.data.split("_")
        platform = parts[1]
        service = parts[2]

        platform_name = platforms.get(platform, platform)

        services = {
            "followers": "👥 متابعين",
            "likes": "❤️ لايكات",
            "views": "👀 مشاهدات",
            "engagement": "🔥 ريتش وتفاعل",
        }

        service_name = services.get(service, service)

        await query.edit_message_text(
            f"{platform_name}\n\n"
            f"الخدمة: {service_name}\n\n"
            "💰 الأسعار والباقات سيتم عرضها هنا.\n\n"
            "📞 للطلب أو الاستفسار تواصل مع الدعم.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="support")],
                [InlineKeyboardButton("🔙 الخدمات", callback_data=f"platform_{platform}")],
            ])
        )
        return

    if query.data == "subscriptions":
        await query.edit_message_text(
            """💻 اشتراكات البرامج

• اشتراكات برامج التصميم
• أدوات الذكاء الاصطناعي
• خدمات رقمية متنوعة

📞 للطلب أو معرفة الأسعار تواصل مع الدعم.""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
            ])
        )
        return

    if query.data == "design":
        await query.edit_message_text(
            """🎨 التصميم والجرافيك

• تصميم بوستات
• هويات بصرية
• إعلانات
• تصميمات سوشيال ميديا

📞 للطلب تواصل مع الدعم.""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
            ])
        )
        return

    if query.data == "support":
        await query.edit_message_text(
            """📞 الدعم

اكتب لنا الخدمة التي تريدها وسنساعدك في إتمام الطلب.""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
            ])
        )
        return

    if query.data == "home":
        await query.edit_message_text(
            WELCOME,
            reply_markup=main_menu()
        )


def run():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("SaQR Agency bot is running...")

    app.run_polling()


if __name__ == "__main__":
    run()
