import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")


WELCOME = """🦅 أهلاً بك في SaQR Agency

نقدم لك مجموعة متكاملة من الخدمات الرقمية والسوشيال ميديا.

اختر القسم الذي تريد معرفة خدماته 👇"""


# =========================
# القائمة الرئيسية
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
# أزرار عامة
# =========================

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 طلب الخدمة", callback_data="order")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


def only_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# خدمات السوشيال ميديا
# =========================

def social_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 متابعين", callback_data="followers")],
        [InlineKeyboardButton("❤️ لايكات", callback_data="likes")],
        [InlineKeyboardButton("👁 مشاهدات", callback_data="views")],
        [InlineKeyboardButton("📈 ريتش وتفاعل", callback_data="reach")],
        [InlineKeyboardButton("🔄 خدمات أخرى", callback_data="social_other")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# اشتراكات البرامج
# =========================

def subscriptions_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 برامج التصميم", callback_data="design_apps")],
        [InlineKeyboardButton("🤖 أدوات الذكاء الاصطناعي", callback_data="ai_apps")],
        [InlineKeyboardButton("🎬 برامج المونتاج", callback_data="editing_apps")],
        [InlineKeyboardButton("💻 برامج وخدمات رقمية", callback_data="digital_apps")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# التصميم والجرافيك
# =========================

def design_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 تصميم بوستات", callback_data="posts")],
        [InlineKeyboardButton("🎯 تصميم لوجو", callback_data="logo")],
        [InlineKeyboardButton("🏢 هوية بصرية", callback_data="branding")],
        [InlineKeyboardButton("📢 تصميم إعلانات", callback_data="ad_design")],
        [InlineKeyboardButton("🖼 تصميمات السوشيال ميديا", callback_data="social_design")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# المواقع والبرمجة
# =========================

def web_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 تصميم المواقع", callback_data="websites")],
        [InlineKeyboardButton("🛒 المتاجر الإلكترونية", callback_data="stores")],
        [InlineKeyboardButton("🤖 برمجة البوتات", callback_data="bots")],
        [InlineKeyboardButton("⚙️ برمجة وتطوير", callback_data="development")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# الإعلانات والتسويق
# =========================

def marketing_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 إعلانات ممولة", callback_data="ads")],
        [InlineKeyboardButton("📱 إدارة صفحات السوشيال", callback_data="page_management")],
        [InlineKeyboardButton("📈 زيادة الوصول والتفاعل", callback_data="growth")],
        [InlineKeyboardButton("🎯 التسويق الرقمي", callback_data="digital_marketing")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]
    ])


# =========================
# أمر البداية
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME,
        reply_markup=main_menu()
    )


# =========================
# التعامل مع الأزرار
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data


    # -------------------------
    # القائمة الرئيسية
    # -------------------------

    if data == "home":
        await query.edit_message_text(
            WELCOME,
            reply_markup=main_menu()
        )
        return


    # -------------------------
    # السوشيال ميديا
    # -------------------------

    if data == "social":
        await query.edit_message_text(
            """📱 خدمات السوشيال ميديا

اختر الخدمة التي تريدها 👇""",
            reply_markup=social_menu()
        )
        return


    if data == "followers":
        text = """👥 خدمة المتابعين

نوفر خدمات زيادة المتابعين لمختلف منصات التواصل الاجتماعي.

📌 مناسبة للحسابات والصفحات المختلفة.

📩 لمعرفة التفاصيل والأسعار اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "likes":
        text = """❤️ خدمة اللايكات

زيادة التفاعل على المنشورات والمحتوى الخاص بك.

📩 لمعرفة التفاصيل والأسعار اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "views":
        text = """👁 خدمة المشاهدات

زيادة مشاهدات الفيديوهات والمحتوى على منصات التواصل.

📩 لمعرفة التفاصيل والأسعار اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "reach":
        text = """📈 الريتش والتفاعل

خدمات تساعد على زيادة الوصول والتفاعل مع المحتوى.

• وصول
• تفاعل
• مشاهدات
• لايكات

📩 لمعرفة التفاصيل والأسعار اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "social_other":
        text = """🔄 خدمات السوشيال ميديا الأخرى

نوفر خدمات متنوعة لمنصات التواصل الاجتماعي.

إذا لم تجد الخدمة التي تبحث عنها، أرسل لنا تفاصيل طلبك وسيساعدك الدعم."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # الاشتراكات
    # -------------------------

    if data == "subscriptions":
        await query.edit_message_text(
            """💻 اشتراكات البرامج والخدمات الرقمية

اختر نوع الاشتراك 👇""",
            reply_markup=subscriptions_menu()
        )
        return


    if data == "design_apps":
        text = """🎨 برامج التصميم

اشتراكات وخدمات للبرامج والأدوات الخاصة بالتصميم والجرافيك.

📩 اضغط طلب الخدمة لمعرفة المتاح والأسعار."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "ai_apps":
        text = """🤖 أدوات الذكاء الاصطناعي

اشتراكات وخدمات خاصة بأدوات الذكاء الاصطناعي.

📩 اضغط طلب الخدمة لمعرفة المتاح والأسعار."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "editing_apps":
        text = """🎬 برامج المونتاج

اشتراكات وخدمات لبرامج وأدوات المونتاج وصناعة المحتوى.

📩 اضغط طلب الخدمة لمعرفة المتاح والأسعار."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "digital_apps":
        text = """💻 الخدمات الرقمية

مجموعة من الاشتراكات والأدوات والخدمات الرقمية.

📩 اضغط طلب الخدمة لمعرفة المتاح والأسعار."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # التصميم
    # -------------------------

    if data == "design":
        await query.edit_message_text(
            """🎨 التصميم والجرافيك

اختر الخدمة التي تريدها 👇""",
            reply_markup=design_menu()
        )
        return


    if data == "posts":
        text = """📱 تصميم بوستات

تصميم بوستات احترافية للسوشيال ميديا.

مناسب لـ:
• Instagram
• Facebook
• WhatsApp
• وغيرها

📩 اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "logo":
        text = """🎯 تصميم لوجو

تصميم شعار احترافي يناسب نشاطك أو البراند الخاص بك.

📩 اضغط طلب الخدمة واذكر اسم النشاط وفكرة التصميم."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "branding":
        text = """🏢 الهوية البصرية

تصميم هوية متكاملة للبراند.

• لوجو
• ألوان
• خطوط
• تطبيقات الهوية
• تصميمات متوافقة

📩 اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "ad_design":
        text = """📢 تصميم الإعلانات

تصميم إعلانات احترافية للحملات والمنشورات.

📩 اضغط طلب الخدمة وأرسل تفاصيل الإعلان."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "social_design":
        text = """🖼 تصميمات السوشيال ميديا

تصميم محتوى بصري احترافي للصفحات والحسابات.

📩 اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # المواقع والبرمجة
    # -------------------------

    if data == "web":
        await query.edit_message_text(
            """🌐 المواقع والبرمجة

اختر الخدمة التي تريدها 👇""",
            reply_markup=web_menu()
        )
        return


    if data == "websites":
        text = """🌐 تصميم المواقع

إنشاء وتصميم مواقع احترافية تناسب نشاطك.

📩 اضغط طلب الخدمة وأرسل فكرة الموقع."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "stores":
        text = """🛒 المتاجر الإلكترونية

إنشاء وتطوير متاجر إلكترونية لبيع المنتجات والخدمات.

📩 اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "bots":
        text = """🤖 برمجة البوتات

إنشاء وتطوير بوتات Telegram وخدمات الأتمتة.

📩 اضغط طلب الخدمة وأرسل فكرة البوت."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "development":
        text = """⚙️ البرمجة والتطوير

تطوير وبرمجة حلول رقمية حسب احتياجات المشروع.

📩 اضغط طلب الخدمة وأرسل تفاصيل المشروع."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # التسويق والإعلانات
    # -------------------------

    if data == "marketing":
        await query.edit_message_text(
            """📢 الإعلانات والتسويق

اختر الخدمة التي تريدها 👇""",
            reply_markup=marketing_menu()
        )
        return


    if data == "ads":
        text = """📢 الإعلانات الممولة

خدمات الإعلانات والحملات التسويقية على منصات التواصل.

📩 اضغط طلب الخدمة وأرسل:
• المنصة
• الهدف
• الميزانية التقريبية"""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "page_management":
        text = """📱 إدارة صفحات السوشيال ميديا

إدارة وتنظيم محتوى الصفحات والحسابات.

📩 اضغط طلب الخدمة لمعرفة التفاصيل."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "growth":
        text = """📈 زيادة الوصول والتفاعل

حلول لتحسين الوصول والتفاعل مع المحتوى.

📩 اضغط طلب الخدمة لمعرفة التفاصيل."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    if data == "digital_marketing":
        text = """🎯 التسويق الرقمي

خدمات وحلول تسويقية تساعد على تطوير حضور البراند الرقمي.

📩 اضغط طلب الخدمة."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # الأسعار
    # -------------------------

    if data == "prices":
        text = """💰 الأسعار والعروض

أسعار الخدمات تختلف حسب نوع الخدمة والكمية والمنصة والمواصفات المطلوبة.

📩 للحصول على السعر الحالي:
اضغط «طلب الخدمة» وأرسل الخدمة التي تريدها بالتحديد.

سنرسل لك التفاصيل والسعر المناسب."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # الدعم
    # -------------------------

    if data == "support":
        text = """📞 التواصل مع الدعم

للتواصل مع فريق SaQR Agency:

أرسل في رسالة واحدة:
• اسم الخدمة
• المنصة
• الكمية المطلوبة
• أي تفاصيل إضافية

وسيتم مساعدتك في إتمام الطلب."""
        await query.edit_message_text(text, reply_markup=back_menu())
        return


    # -------------------------
    # طلب الخدمة
    # -------------------------

    if data == "order":
        text = """📩 طلب خدمة

أرسل لنا الآن:

1️⃣ اسم الخدمة
2️⃣ المنصة المطلوبة
3️⃣ الكمية أو التفاصيل
4️⃣ أي ملاحظات إضافية

مثال:

الخدمة: متابعين
المنصة: Instagram
الكمية: 10,000
التفاصيل: أريد معرفة السعر

وسيتم الرد عليك من فريق الدعم."""
        await query.edit_message_text(text, reply_markup=only_back())
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
