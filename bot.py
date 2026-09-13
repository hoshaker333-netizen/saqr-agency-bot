import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")


WELCOME = """🦅 أهلاً بك في SaQR Agency

نقدم لك خدمات رقمية متكاملة:
📱 سوشيال ميديا
💻 اشتراكات برامج
🎨 تصميم وجرافيك
🌐 مواقع وبرمجة
📢 إعلانات وتسويق

اختر القسم الذي تريد معرفة خدماته 👇"""


# =========================
# القوائم الرئيسية
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 خدمات السوشيال ميديا", callback_data="social")],
        [InlineKeyboardButton("💻 اشتراكات البرامج", callback_data="subscriptions")],
        [InlineKeyboardButton("🎨 التصميم والجرافيك", callback_data="design")],
        [InlineKeyboardButton("🌐 المواقع والبرمجة", callback_data="web")],
        [InlineKeyboardButton("📢 الإعلانات والتسويق", callback_data="marketing")],
        [InlineKeyboardButton("💰 الأسعار والعروض", callback_data="prices")],
        [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="support")],
    ])


# =========================
# السوشيال ميديا
# =========================

def social_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 متابعين", callback_data="followers")],
        [InlineKeyboardButton("❤️ لايكات", callback_data="likes")],
        [InlineKeyboardButton("👁️ مشاهدات", callback_data="views")],
        [InlineKeyboardButton("📈 ريتش وتفاعل", callback_data="reach")],
        [InlineKeyboardButton("➕ خدمات أخرى", callback_data="social_other")],
        [InlineKeyboardButton("🛒 طلب خدمة", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# الاشتراكات
# =========================

def subscriptions_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 برامج التصميم", callback_data="design_apps")],
        [InlineKeyboardButton("🤖 أدوات الذكاء الاصطناعي", callback_data="ai_tools")],
        [InlineKeyboardButton("🎬 برامج المونتاج", callback_data="editing_apps")],
        [InlineKeyboardButton("💻 خدمات رقمية", callback_data="digital_services")],
        [InlineKeyboardButton("🛒 طلب اشتراك", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# التصميم والجرافيك
# =========================

def design_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ تصميم بوستات", callback_data="posts")],
        [InlineKeyboardButton("✨ تصميم لوجو", callback_data="logo")],
        [InlineKeyboardButton("🎯 هوية بصرية", callback_data="branding")],
        [InlineKeyboardButton("📢 تصميم إعلانات", callback_data="ad_design")],
        [InlineKeyboardButton("📱 تصميمات سوشيال ميديا", callback_data="social_design")],
        [InlineKeyboardButton("🛒 طلب تصميم", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# المواقع والبرمجة
# =========================

def web_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 تصميم مواقع", callback_data="websites")],
        [InlineKeyboardButton("🛍️ متاجر إلكترونية", callback_data="stores")],
        [InlineKeyboardButton("🤖 بوتات تيليجرام", callback_data="telegram_bots")],
        [InlineKeyboardButton("💻 برمجة وتطوير", callback_data="development")],
        [InlineKeyboardButton("🛒 طلب خدمة", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# الإعلانات والتسويق
# =========================

def marketing_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 الإعلانات الممولة", callback_data="paid_ads")],
        [InlineKeyboardButton("📱 إدارة الصفحات", callback_data="page_management")],
        [InlineKeyboardButton("📈 تنمية الحسابات", callback_data="growth")],
        [InlineKeyboardButton("🎯 التسويق الرقمي", callback_data="digital_marketing")],
        [InlineKeyboardButton("🛒 طلب خدمة", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# زر الرجوع
# =========================

def back_menu(callback_data="home"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 طلب الخدمة", callback_data="order")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=callback_data)],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home")],
    ])


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME,
        reply_markup=main_menu()
    )


# =========================
# التعامل مع الأزرار
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    data = query.data

    # القائمة الرئيسية
    if data == "home":
        await query.edit_message_text(
            WELCOME,
            reply_markup=main_menu()
        )
        return

    # =====================
    # الأقسام الرئيسية
    # =====================

    if data == "social":
        text = """📱 خدمات السوشيال ميديا

نوفر خدمات متنوعة لمنصات التواصل الاجتماعي:

👥 متابعين
❤️ لايكات
👁️ مشاهدات
📈 ريتش وتفاعل
➕ خدمات أخرى

اختر الخدمة التي تريدها 👇"""

        await query.edit_message_text(
            text,
            reply_markup=social_menu()
        )
        return

    if data == "subscriptions":
        text = """💻 اشتراكات البرامج

نوفر اشتراكات وخدمات رقمية متنوعة:

🎨 برامج التصميم
🤖 أدوات الذكاء الاصطناعي
🎬 برامج المونتاج
💻 خدمات رقمية متنوعة

اختر القسم الذي تريد معرفة تفاصيله 👇"""

        await query.edit_message_text(
            text,
            reply_markup=subscriptions_menu()
        )
        return

    if data == "design":
        text = """🎨 التصميم والجرافيك

خدمات تصميم احترافية:

🖼️ تصميم بوستات
✨ تصميم لوجو
🎯 هوية بصرية
📢 تصميم إعلانات
📱 تصميمات سوشيال ميديا

اختر الخدمة التي تريدها 👇"""

        await query.edit_message_text(
            text,
            reply_markup=design_menu()
        )
        return

    if data == "web":
        text = """🌐 المواقع والبرمجة

خدمات الويب والبرمجة:

🌐 تصميم مواقع
🛍️ متاجر إلكترونية
🤖 بوتات تيليجرام
💻 برمجة وتطوير

اختر الخدمة التي تريدها 👇"""

        await query.edit_message_text(
            text,
            reply_markup=web_menu()
        )
        return

    if data == "marketing":
        text = """📢 الإعلانات والتسويق

خدمات التسويق الرقمي:

📣 الإعلانات الممولة
📱 إدارة الصفحات
📈 تنمية الحسابات
🎯 التسويق الرقمي

اختر الخدمة التي تريدها 👇"""

        await query.edit_message_text(
            text,
            reply_markup=marketing_menu()
        )
        return

    if data == "prices":
        text = """💰 الأسعار والعروض

الأسعار تختلف حسب نوع الخدمة والكمية والمنصة.

📌 للحصول على السعر الحالي:
اضغط على «🛒 طلب الخدمة» وأرسل تفاصيل طلبك.

سنحدد لك الخدمة والسعر المناسب."""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 طلب خدمة", callback_data="order")],
                [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="support")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
            ])
        )
        return

    if data == "support":
        text = """📞 التواصل مع الدعم

للطلب أو الاستفسار أرسل لنا:

• اسم الخدمة
• المنصة
• الكمية أو التفاصيل المطلوبة
• أي ملاحظات إضافية

وسنساعدك في إتمام طلبك."""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 طلب خدمة", callback_data="order")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
            ])
        )
        return

    # =====================
    # خدمات السوشيال
    # =====================

    social_services = {
        "followers": """👥 المتابعين

خدمة زيادة المتابعين للحسابات والمنصات المختلفة.

📌 اختر «طلب خدمة» لإرسال المنصة والكمية المطلوبة.""",

        "likes": """❤️ اللايكات

خدمة زيادة الإعجابات والتفاعل على المحتوى.

📌 اختر «طلب خدمة» لإرسال المنصة والرابط والكمية.""",

        "views": """👁️ المشاهدات

خدمة زيادة المشاهدات للمحتوى على المنصات المختلفة.

📌 اختر «طلب خدمة» لإرسال الرابط والكمية المطلوبة.""",

        "reach": """📈 الريتش والتفاعل

خدمات خاصة بزيادة الوصول والتفاعل حسب نوع المنصة والحملة.

📌 اختر «طلب خدمة» لإرسال التفاصيل.""",

        "social_other": """➕ خدمات أخرى

إذا لم تجد الخدمة التي تبحث عنها، أرسل تفاصيل طلبك وسنساعدك في تحديد الخدمة المناسبة."""
    }

    if data in social_services:
        await query.edit_message_text(
            social_services[data],
            reply_markup=back_menu("social")
        )
        return

    # =====================
    # الاشتراكات
    # =====================

    subscription_services = {
        "design_apps": """🎨 برامج التصميم

اشتراكات وخدمات متعلقة ببرامج التصميم والجرافيك.

📌 لمعرفة المتاح والسعر الحالي أرسل اسم البرنامج.""",

        "ai_tools": """🤖 أدوات الذكاء الاصطناعي

اشتراكات وخدمات لأدوات الذكاء الاصطناعي المختلفة.

📌 أرسل اسم الأداة التي تريدها لمعرفة المتاح والسعر.""",

        "editing_apps": """🎬 برامج المونتاج

اشتراكات وخدمات لبرامج المونتاج وتحرير الفيديو.

📌 أرسل اسم البرنامج المطلوب.""",

        "digital_services": """💻 خدمات رقمية

خدمات رقمية متنوعة حسب احتياجك.

📌 أرسل تفاصيل الخدمة المطلوبة وسنساعدك."""
    }

    if data in subscription_services:
        await query.edit_message_text(
            subscription_services[data],
            reply_markup=back_menu("subscriptions")
        )
        return

    # =====================
    # التصميم
    # =====================

    design_services = {
        "posts": "🖼️ تصميم بوستات\n\nتصميم بوستات احترافية للسوشيال ميديا حسب الهوية والمحتوى المطلوب.",
        "logo": "✨ تصميم لوجو\n\nتصميم شعار احترافي مناسب للعلامة التجارية والاستخدامات المختلفة.",
        "branding": "🎯 الهوية البصرية\n\nتصميم هوية بصرية متكاملة للعلامة التجارية.",
        "ad_design": "📢 تصميم إعلانات\n\nتصميم إعلانات ومواد بصرية للحملات التسويقية.",
        "social_design": "📱 تصميمات سوشيال ميديا\n\nتصميم محتوى بصري مناسب لمنصات التواصل الاجتماعي."
    }

    if data in design_services:
        await query.edit_message_text(
            design_services[data],
            reply_markup=back_menu("design")
        )
        return

    # =====================
    # المواقع والبرمجة
    # =====================

    web_services = {
        "websites": "🌐 تصميم مواقع\n\nإنشاء وتصميم مواقع احترافية حسب احتياجات المشروع.",
        "stores": "🛍️ المتاجر الإلكترونية\n\nتصميم وتطوير متاجر إلكترونية لبيع المنتجات والخدمات.",
        "telegram_bots": "🤖 بوتات تيليجرام\n\nإنشاء وتطوير بوتات تيليجرام حسب فكرة المشروع.",
        "development": "💻 البرمجة والتطوير\n\nخدمات برمجة وتطوير حسب متطلبات المشروع."
    }

    if data in web_services:
        await query.edit_message_text(
            web_services[data],
            reply_markup=back_menu("web")
        )
        return

    # =====================
    # التسويق
    # =====================

    marketing_services = {
        "paid_ads": "📣 الإعلانات الممولة\n\nإعداد وإدارة الحملات الإعلانية حسب الهدف والمنصة.",
        "page_management": "📱 إدارة الصفحات\n\nخدمات إدارة وتنظيم محتوى صفحات التواصل الاجتماعي.",
        "growth": "📈 تنمية الحسابات\n\nخطط وخدمات تساعد على تطوير ونمو الحسابات.",
        "digital_marketing": "🎯 التسويق الرقمي\n\nحلول تسويقية رقمية حسب نشاط المشروع والهدف."
    }

    if data in marketing_services:
        await query.edit_message_text(
            marketing_services[data],
            reply_markup=back_menu("marketing")
        )
        return

    # =====================
    # طلب الخدمة
    # =====================

    if data == "order":
        text = """🛒 طلب خدمة

أرسل لنا رسالة تحتوي على:

1️⃣ اسم الخدمة
2️⃣ المنصة
3️⃣ الرابط إن وجد
4️⃣ الكمية أو المدة
5️⃣ أي تفاصيل أو ملاحظات

مثال:

الخدمة: متابعين
المنصة: Instagram
الكمية: 10,000
الرابط: ...
ملاحظات: ...

📩 أرسل التفاصيل وسنقوم بمساعدتك."""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 الدعم", callback_data="support")],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home")],
            ])
        )
        return


# =========================
# تشغيل البوت
# =========================

def run():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("SaQR Agency bot is running...")

    app.run_polling()


if __name__ == "__main__":
    run()
