import os
import sqlite3
import asyncio
import json
import urllib.parse
import urllib.request
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ALKABOS_API_KEY = os.getenv("ALKABOS_API_KEY", "").strip()
XPRO_API_KEY = os.getenv("XPRO_API_KEY", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)

PAYMENT_NAME = os.getenv(
    "PAYMENT_NAME",
    "Hosam Shaker"
).strip()

PAYMENT_METHOD = os.getenv(
    "PAYMENT_METHOD",
    "Vodafone Cash"
).strip()

PAYMENT_NUMBER = os.getenv(
    "PAYMENT_NUMBER",
    ""
).strip()

PROFIT_MARGIN = float(
    os.getenv("PROFIT_MARGIN", "70") or 70
)

ALKABOS_API_URL = "https://alkabos.com/api/v2"
XPRO_API_URL = "https://xprostore.store/api/v1"

# Persistent Deployka storage
DB_FILE = "/data/bot.db"

# Fallback only.
# The bot will try to fetch the current rate automatically.
FALLBACK_USD_EGP = 51.36


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")

if not ALKABOS_API_KEY:
    raise RuntimeError("ALKABOS_API_KEY is not set.")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID is not set.")


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            provider TEXT,
            service_id TEXT,
            service_name TEXT,
            category TEXT,
            link TEXT,
            quantity INTEGER,
            cost REAL,
            sale_price REAL,
            payment_status TEXT,
            order_status TEXT,
            provider_order_id TEXT,
            proof_file_id TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HTTP
# =========================================================

def http_post_form(url, params, headers=None):
    data = urllib.parse.urlencode(params).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers=headers or {}
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return response.read().decode("utf-8")


def http_get(url, headers=None):
    request = urllib.request.Request(
        url,
        method="GET",
        headers=headers or {}
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return response.read().decode("utf-8")


# =========================================================
# ALKABOS
# =========================================================

async def alkabos_request(action, extra=None):

    params = {
        "key": ALKABOS_API_KEY,
        "action": action,
    }

    if extra:
        params.update(extra)

    try:
        raw = await asyncio.to_thread(
            http_post_form,
            ALKABOS_API_URL,
            params,
            {
                "Content-Type":
                    "application/x-www-form-urlencoded",
                "User-Agent":
                    "SaQR-Agency-Bot/2.0",
            }
        )

        return json.loads(raw)

    except Exception as e:
        print("Alkabos error:", e)
        return None


async def get_alkabos_services():

    result = await alkabos_request("services")

    if isinstance(result, list):
        return result

    return []


async def create_alkabos_order(
    service_id,
    link,
    quantity
):

    return await alkabos_request(
        "add",
        {
            "service": service_id,
            "link": link,
            "quantity": quantity,
        }
    )


async def get_alkabos_status(order_id):

    return await alkabos_request(
        "status",
        {
            "order": order_id
        }
    )


async def get_alkabos_balance():

    return await alkabos_request("balance")


# =========================================================
# USD -> EGP
# =========================================================

async def get_usd_egp_rate():

    urls = [
        "https://api.frankfurter.dev/v2/"
        "providers/cbe/rate/usd/egp",

        "https://api.frankfurter.dev/v2/"
        "rate/usd/egp",
    ]

    for url in urls:

        try:

            raw = await asyncio.to_thread(
                http_get,
                url
            )

            data = json.loads(raw)

            rate = data.get("rate")

            if rate:
                return float(rate)

        except Exception as e:
            print("Exchange rate error:", e)

    return FALLBACK_USD_EGP


async def calculate_price(
    provider_rate,
    quantity
):

    usd_egp = await get_usd_egp_rate()

    provider_cost_egp = (
        float(provider_rate)
        * int(quantity)
        / 1000
        * usd_egp
    )

    sale_price = (
        provider_cost_egp
        * (1 + PROFIT_MARGIN / 100)
    )

    return (
        round(provider_cost_egp, 2),
        round(sale_price, 2),
        round(usd_egp, 4)
    )


# =========================================================
# X PRO STORE
# =========================================================

async def xpro_request(
    method,
    endpoint,
    payload=None
):

    if not XPRO_API_KEY:
        return None

    url = XPRO_API_URL + endpoint

    headers = {
        "Authorization":
            f"Bearer {XPRO_API_KEY}",
        "Content-Type":
            "application/json",
        "User-Agent":
            "SaQR-Agency-Bot/2.0",
    }

    try:

        if method == "GET":

            raw = await asyncio.to_thread(
                http_get,
                url,
                headers
            )

        else:

            data = json.dumps(
                payload or {}
            ).encode("utf-8")

            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers=headers
            )

            raw = await asyncio.to_thread(
                lambda: urllib.request.urlopen(
                    request,
                    timeout=30
                ).read().decode("utf-8")
            )

        return json.loads(raw)

    except Exception as e:
        print("XPro error:", e)
        return None


async def get_xpro_services():

    result = await xpro_request(
        "GET",
        "/services"
    )

    if isinstance(result, list):
        return result

    if isinstance(result, dict):

        for key in (
            "services",
            "data",
            "results"
        ):

            if isinstance(
                result.get(key),
                list
            ):
                return result[key]

    return []


async def create_xpro_order(
    service_id,
    quantity
):

    return await xpro_request(
        "POST",
        "/orders",
        {
            "service_id": str(service_id),
            "quantity": int(quantity),
        }
    )


# =========================================================
# CUSTOMER CATALOG
# =========================================================

# ---------------------------------------------------------
# SOCIAL MEDIA
#
# هنا نربط اسم SaQR بالـAlkabos service ID.
#
# service_id = رقم الخدمة عند Alkabos
# name       = الاسم الذي يراه العميل
# description= الوصف الذي يراه العميل
# ---------------------------------------------------------

SOCIAL_CATALOG = {

    "instagram": {
        "title": "📸 Instagram",
        "services": []
    },

    "tiktok": {
        "title": "🎵 TikTok",
        "services": []
    },

    "facebook": {
        "title": "🔵 Facebook",
        "services": []
    },

    "youtube": {
        "title": "▶️ YouTube",
        "services": []
    },

    "telegram": {
        "title": "✈️ Telegram",
        "services": []
    },

    "whatsapp": {
        "title": "🟢 WhatsApp",
        "services": []
    },

    "x": {
        "title": "𝕏 X / Twitter",
        "services": []
    },

    "snapchat": {
        "title": "👻 Snapchat",
        "services": []
    },

    "twitch": {
        "title": "🎮 Twitch",
        "services": []
    },

    "linkedin": {
        "title": "💼 LinkedIn",
        "services": []
    },

    "websites": {
        "title": "🌐 المواقع والمتاجر",
        "services": []
    },

    "marketing": {
        "title": "📢 التسويق والإعلانات",
        "services": []
    },
}


# ---------------------------------------------------------
# PROGRAMS
#
# X Pro Store service IDs are kept here.
# Customer sees only SaQR names.
# ---------------------------------------------------------

PROGRAM_CATALOG = {

    "ai": {
        "title": "🤖 الذكاء الاصطناعي",
        "services": []
    },

    "video": {
        "title": "🎬 المونتاج والفيديو",
        "services": []
    },

    "design": {
        "title": "🎨 التصميم والجرافيك",
        "services": []
    },

    "audio": {
        "title": "🎵 الصوت والموسيقى",
        "services": []
    },

    "productivity": {
        "title": "📝 الإنتاجية والعمل",
        "services": []
    },

    "education": {
        "title": "📚 التعليم والكورسات",
        "services": []
    },

    "vpn": {
        "title": "🔐 VPN والأمان",
        "services": []
    },

    "entertainment": {
        "title": "🎞️ الترفيه والمنصات",
        "services": []
    },

    "tools": {
        "title": "🧰 أدوات وخدمات متنوعة",
        "services": []
    },
}


# =========================================================
# EXAMPLE SERVICE STRUCTURE
# =========================================================

"""
مثال:

SOCIAL_CATALOG["facebook"]["services"] = [
    {
        "service_id": "3400",
        "name": "ريأكت فيسبوك مصريين",
        "description": "تفاعل على منشورات فيسبوك...",
    }
]

PROGRAM_CATALOG["ai"]["services"] = [
    {
        "service_id": "13",
        "name": "ChatGPT Plus",
        "description": "اشتراك ChatGPT...",
        "price": 150,
        "quantity": 1,
        "provider": "xpro"
    }
]

سنملأ هذه القائمة بعد الحصول على الخدمات
الفعلية من الموردين.
"""


# =========================================================
# MAIN MENU
# =========================================================

WELCOME = """🦅 أهلاً بك في SaQR Agency

متجر الخدمات الرقمية الخاص بك.

اختر القسم الذي تريد الدخول إليه 👇"""


def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💻 البرامج والاشتراكات",
                callback_data="programs"
            )
        ],

        [
            InlineKeyboardButton(
                "📱 السوشيال ميديا والماركتينج",
                callback_data="social"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 طلباتي",
                callback_data="my_orders"
            )
        ],

        [
            InlineKeyboardButton(
                "🎧 الدعم",
                callback_data="support"
            )
        ],
    ])


# =========================================================
# CATEGORY MENUS
# =========================================================

def catalog_keyboard(
    catalog,
    prefix
):

    buttons = []

    for key, category in catalog.items():

        buttons.append([
            InlineKeyboardButton(
                category["title"],
                callback_data=f"{prefix}:{key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# =========================================================
# PROGRAM SERVICES
# =========================================================

def program_services_keyboard(
    category_key
):

    category = PROGRAM_CATALOG.get(
        category_key
    )

    if not category:
        return catalog_keyboard(
            PROGRAM_CATALOG,
            "programcat"
        )

    buttons = []

    for index, service in enumerate(
        category["services"]
    ):

        buttons.append([
            InlineKeyboardButton(
                f"🛒 {service['name']}",
                callback_data=
                f"programservice:{category_key}:{index}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 التصنيفات",
            callback_data="programs"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# =========================================================
# SOCIAL SERVICES
# =========================================================

def social_services_keyboard(
    category_key
):

    category = SOCIAL_CATALOG.get(
        category_key
    )

    if not category:
        return catalog_keyboard(
            SOCIAL_CATALOG,
            "socialcat"
        )

    buttons = []

    for index, service in enumerate(
        category["services"]
    ):

        buttons.append([
            InlineKeyboardButton(
                f"🛒 {service['name']}",
                callback_data=
                f"socialservice:{category_key}:{index}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 المنصات",
            callback_data="social"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# =========================================================
# SERVICE DETAILS
# =========================================================

async def program_details(
    service
):

    price = service.get(
        "price",
        0
    )

    duration = service.get(
        "duration",
        ""
    )

    description = service.get(
        "description",
        ""
    )

    text = f"""💻 {service['name']}

"""

    if description:
        text += (
            f"📝 {description}\n\n"
        )

    if duration:
        text += (
            f"⏳ المدة: {duration}\n"
        )

    text += (
        f"\n💰 السعر: "
        f"{float(price):.2f} جنيه\n"
    )

    text += """
━━━━━━━━━━━━━━

اختر ما تريد فعله 👇"""

    return text


async def social_details(
    service
):

    service_id = str(
        service["service_id"]
    )

    provider_service = find_alkabos_service(
        service_id
    )

    if not provider_service:
        return "❌ الخدمة غير متاحة حاليًا."

    minimum = int(
        float(
            provider_service.get(
                "min",
                1
            )
        )
    )

    maximum = int(
        float(
            provider_service.get(
                "max",
                1
            )
        )
    )

    rate = float(
        provider_service.get(
            "rate",
            0
        )
    )

    cost, sale, usd_egp = (
        await calculate_price(
            rate,
            minimum
        )
    )

    # السعر هنا محسوب على الحد الأدنى.
    # السعر الحقيقي أثناء الطلب يعاد حسابه بالكمية.

    text = f"""📱 {service['name']}

"""

    if service.get("description"):
        text += (
            f"📝 {service['description']}\n\n"
        )

    text += f"""📦 الحد الأدنى: {minimum}
📦 الحد الأقصى: {maximum}

💰 السعر: يبدأ من {sale:.2f} جنيه لكل {minimum}

━━━━━━━━━━━━━━

اختر ما تريد فعله 👇"""

    return text


# =========================================================
# ALKABOS SERVICE CACHE
# =========================================================

ALKABOS_SERVICES = []


async def refresh_alkabos():

    global ALKABOS_SERVICES

    services = await get_alkabos_services()

    if services:
        ALKABOS_SERVICES = services

    return ALKABOS_SERVICES


def find_alkabos_service(
    service_id
):

    for service in ALKABOS_SERVICES:

        if str(
            service.get("service")
        ) == str(service_id):

            return service

    return None


# =========================================================
# PROGRAM SERVICE
# =========================================================

def get_program_service(
    category_key,
    index
):

    category = PROGRAM_CATALOG.get(
        category_key
    )

    if not category:
        return None

    services = category["services"]

    if index >= len(services):
        return None

    return services[index]


# =========================================================
# SOCIAL SERVICE
# =========================================================

def get_social_service(
    category_key,
    index
):

    category = SOCIAL_CATALOG.get(
        category_key
    )

    if not category:
        return None

    services = category["services"]

    if index >= len(services):
        return None

    return services[index]


# =========================================================
# START ORDER
# =========================================================

async def start_social_order(
    query,
    context,
    category_key,
    index
):

    service = get_social_service(
        category_key,
        index
    )

    if not service:
        await query.message.reply_text(
            "❌ الخدمة غير موجودة."
        )
        return

    provider = find_alkabos_service(
        service["service_id"]
    )

    if not provider:
        await query.message.reply_text(
            "❌ الخدمة غير متاحة حاليًا."
        )
        return

    minimum = int(
        float(provider.get("min", 1))
    )

    maximum = int(
        float(provider.get("max", 1))
    )

    context.user_data["order"] = {
        "provider": "alkabos",
        "service_id":
            service["service_id"],
        "service_name":
            service["name"],
        "category":
            category_key,
        "minimum":
            minimum,
        "maximum":
            maximum,
    }

    await query.message.reply_text(
        f"""🛒 طلب الخدمة

الخدمة:
{service['name']}

📦 الحد الأدنى: {minimum}
📦 الحد الأقصى: {maximum}

✍️ أرسل الكمية الآن:

مثال:
1000"""
    )


async def start_program_order(
    query,
    context,
    category_key,
    index
):

    service = get_program_service(
        category_key,
        index
    )

    if not service:
        await query.message.reply_text(
            "❌ الخدمة غير موجودة."
        )
        return

    quantity = int(
        service.get(
            "quantity",
            1
        )
    )

    price = float(
        service.get(
            "price",
            0
        )
    )

    context.user_data["order"] = {
        "provider": "xpro",
        "service_id":
            str(service["service_id"]),
        "service_name":
            service["name"],
        "category":
            category_key,
        "quantity":
            quantity,
        "cost":
            float(
                service.get(
                    "cost",
                    0
                )
            ),
        "sale_price":
            price,
        "needs_link":
            bool(
                service.get(
                    "needs_link",
                    False
                )
            ),
    }

    if service.get(
        "needs_link",
        False
    ):

        context.user_data[
            "waiting_program_link"
        ] = True

        await query.message.reply_text(
            f"""🛒 {service['name']}

💰 السعر:
{price:.2f} جنيه

🔗 أرسل البيانات المطلوبة للخدمة الآن."""
        )

        return

    await show_payment(
        query.message,
        context,
        context.user_data["order"]
    )


# =========================================================
# PAYMENT
# =========================================================

async def show_payment(
    message,
    context,
    order_data
):

    sale_price = float(
        order_data["sale_price"]
    )

    text = f"""💳 الدفع

🧾 الخدمة:
{order_data["service_name"]}

📦 الكمية:
{order_data["quantity"]}

💰 الإجمالي:
{sale_price:.2f} جنيه

━━━━━━━━━━━━━━

طريقة الدفع:
{PAYMENT_METHOD}

اسم المستلم:
{PAYMENT_NAME}

رقم التحويل:
{PAYMENT_NUMBER}

━━━━━━━━━━━━━━

بعد التحويل اضغط:

✅ أرسلت التحويل

ثم أرسل صورة إثبات الدفع."""

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "✅ أرسلت التحويل",
                callback_data="payment_sent"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data="home"
            )
        ],

    ])

    await message.reply_text(
        text,
        reply_markup=keyboard
    )


# =========================================================
# SAVE ORDER
# =========================================================

def save_order(
    user,
    order_data,
    proof_file_id=""
):

    conn = db()

    cursor = conn.execute("""
        INSERT INTO orders (
            user_id,
            username,
            provider,
            service_id,
            service_name,
            category,
            link,
            quantity,
            cost,
            sale_price,
            payment_status,
            order_status,
            provider_order_id,
            proof_file_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        user.id,

        user.username or "",

        order_data["provider"],

        order_data["service_id"],

        order_data["service_name"],

        order_data.get(
            "category",
            ""
        ),

        order_data.get(
            "link",
            ""
        ),

        order_data["quantity"],

        order_data.get(
            "cost",
            0
        ),

        order_data["sale_price"],

        "pending",

        "waiting_payment",

        "",

        proof_file_id,

        datetime.now().isoformat(),

    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id


# =========================================================
# ADMIN NOTIFICATION
# =========================================================

async def notify_admin(
    context,
    order_id
):

    conn = db()

    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    conn.close()

    if not row:
        return

    text = f"""🔔 طلب دفع جديد

🆔 #SAQ-{row["id"]:05d}

👤 العميل:
{row["username"] or "بدون Username"}

🆔 Telegram ID:
{row["user_id"]}

━━━━━━━━━━━━━━

🛒 الخدمة:
{row["service_name"]}

📦 الكمية:
{row["quantity"]}

🔗 الرابط:
{row["link"] or "غير مطلوب"}

💰 التكلفة:
{row["cost"]:.2f} جنيه

💵 سعر البيع:
{row["sale_price"]:.2f} جنيه

📈 هامش الربح:
{PROFIT_MARGIN}%

🏷️ المورد:
{row["provider"]}

━━━━━━━━━━━━━━

💳 في انتظار مراجعة الدفع."""

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "✅ تأكيد الدفع وتنفيذ",
                callback_data=
                f"approve:{order_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ رفض الدفع",
                callback_data=
                f"reject:{order_id}"
            )
        ],

    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=keyboard
    )

    if row["proof_file_id"]:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=row["proof_file_id"],
            caption=
            f"🧾 إثبات الدفع "
            f"#SAQ-{row['id']:05d}"
        )


# =========================================================
# CALLBACK
# =========================================================

async def callback_handler(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    data = query.data

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":

        await query.message.reply_text(
            WELCOME,
            reply_markup=main_menu()
        )

        return

    # -----------------------------------------------------
    # PROGRAMS
    # -----------------------------------------------------

    if data == "programs":

        await query.message.reply_text(
            "💻 البرامج والاشتراكات\n\n"
            "اختر التصنيف:",
            reply_markup=catalog_keyboard(
                PROGRAM_CATALOG,
                "programcat"
            )
        )

        return

    if data.startswith(
        "programcat:"
    ):

        category_key = data.split(
            ":",
            1
        )[1]

        category = PROGRAM_CATALOG.get(
            category_key
        )

        if not category:
            return

        if not category["services"]:

            await query.message.reply_text(
                f"{category['title']}\n\n"
                "⏳ لا توجد خدمات مضافة "
                "في هذا التصنيف حاليًا."
            )

            return

        await query.message.reply_text(
            category["title"] +
            "\n\nاختر الخدمة:",
            reply_markup=
            program_services_keyboard(
                category_key
            )
        )

        return

    if data.startswith(
        "programservice:"
    ):

        _, category_key, index = (
            data.split(":")
        )

        service = get_program_service(
            category_key,
            int(index)
        )

        if not service:
            return

        text = await program_details(
            service
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🛒 شراء الخدمة",
                    callback_data=
                    f"buyprogram:{category_key}:{index}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data=
                    f"programcat:{category_key}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ],

        ])

        await query.message.reply_text(
            text,
            reply_markup=keyboard
        )

        return

    if data.startswith(
        "buyprogram:"
    ):

        _, category_key, index = (
            data.split(":")
        )

        await start_program_order(
            query,
            context,
            category_key,
            int(index)
        )

        return

    # -----------------------------------------------------
    # SOCIAL
    # -----------------------------------------------------

    if data == "social":

        await query.message.reply_text(
            "📱 السوشيال ميديا والماركتينج\n\n"
            "اختر المنصة:",
            reply_markup=catalog_keyboard(
                SOCIAL_CATALOG,
                "socialcat"
            )
        )

        return

    if data.startswith(
        "socialcat:"
    ):

        category_key = data.split(
            ":",
            1
        )[1]

        category = SOCIAL_CATALOG.get(
            category_key
        )

        if not category:
            return

        if not category["services"]:

            await query.message.reply_text(
                f"{category['title']}\n\n"
                "⏳ لا توجد خدمات مضافة "
                "في هذا التصنيف حاليًا."
            )

            return

        await query.message.reply_text(
            category["title"] +
            "\n\nاختر الخدمة:",
            reply_markup=
            social_services_keyboard(
                category_key
            )
        )

        return

    if data.startswith(
        "socialservice:"
    ):

        _, category_key, index = (
            data.split(":")
        )

        service = get_social_service(
            category_key,
            int(index)
        )

        if not service:
            return

        text = await social_details(
            service
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🛒 شراء الخدمة",
                    callback_data=
                    f"buysocial:{category_key}:{index}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data=
                    f"socialcat:{category_key}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ],

        ])

        await query.message.reply_text(
            text,
            reply_markup=keyboard
        )

        return

    if data.startswith(
        "buysocial:"
    ):

        _, category_key, index = (
            data.split(":")
        )

        await refresh_alkabos()

        await start_social_order(
            query,
            context,
            category_key,
            int(index)
        )

        return

    # -----------------------------------------------------
    # PAYMENT SENT
    # -----------------------------------------------------

    if data == "payment_sent":

        order = context.user_data.get(
            "order"
        )

        if not order:

            await query.message.reply_text(
                "❌ لا يوجد طلب مفتوح."
            )

            return

        context.user_data[
            "waiting_proof"
        ] = True

        await query.message.reply_text(
            """🧾 إثبات الدفع

أرسل الآن صورة واضحة لإيصال التحويل.

⚠️ يجب أن تكون الصورة واضحة وتظهر قيمة التحويل."""
        )

        return

    # -----------------------------------------------------
    # ADMIN APPROVE
    # -----------------------------------------------------

    if data.startswith(
        "approve:"
    ):

        if query.from_user.id != ADMIN_ID:

            await query.message.reply_text(
                "❌ غير مصرح."
            )

            return

        order_id = int(
            data.split(":")[1]
        )

        conn = db()

        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if not row:

            conn.close()

            await query.message.reply_text(
                "❌ الطلب غير موجود."
            )

            return

        if row["payment_status"] == "approved":

            conn.close()

            await query.message.reply_text(
                "⚠️ تم اعتماد الطلب بالفعل."
            )

            return

        # -------------------------------------------------
        # X PRO STORE
        # -------------------------------------------------

        if row["provider"] == "xpro":

            if not XPRO_API_KEY:

                conn.close()

                await query.message.reply_text(
                    "❌ X Pro Store API غير مفعّل."
                )

                return

            result = await create_xpro_order(
                row["service_id"],
                row["quantity"]
            )

        # -------------------------------------------------
        # ALKABOS
        # -------------------------------------------------

        else:

            result = await create_alkabos_order(
                row["service_id"],
                row["link"],
                row["quantity"]
            )

        if not result:

            conn.close()

            await query.message.reply_text(
                "❌ فشل الاتصال بمزود الخدمة."
            )

            return

        # Try common provider order fields
        provider_order_id = (
            result.get("order")
            or result.get("order_id")
            or result.get("id")
        )

        if not provider_order_id:

            conn.close()

            await query.message.reply_text(
                "⚠️ المزود لم يرجع رقم الطلب.\n\n"
                f"الرد:\n{result}"
            )

            return

        conn.execute("""
            UPDATE orders
            SET payment_status = 'approved',
                order_status = 'processing',
                provider_order_id = ?
            WHERE id = ?
        """, (
            str(provider_order_id),
            order_id
        ))

        conn.commit()
        conn.close()

        await query.message.reply_text(
            f"""✅ تم تنفيذ الطلب

🆔 #SAQ-{order_id:05d}

📦 رقم طلب المورد:
{provider_order_id}"""
        )

        try:

            await context.bot.send_message(
                chat_id=row["user_id"],
                text=f"""✅ تم تنفيذ طلبك

🆔 رقم الطلب:
#SAQ-{order_id:05d}

🛒 الخدمة:
{row["service_name"]}

📦 الكمية:
{row["quantity"]}

⏳ الحالة:
جاري التنفيذ."""
            )

        except Exception as e:
            print(
                "Customer notify error:",
                e
            )

        return

    # -----------------------------------------------------
    # ADMIN REJECT
    # -----------------------------------------------------

    if data.startswith(
        "reject:"
    ):

        if query.from_user.id != ADMIN_ID:

            await query.message.reply_text(
                "❌ غير مصرح."
            )

            return

        order_id = int(
            data.split(":")[1]
        )

        conn = db()

        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if not row:

            conn.close()

            return

        conn.execute("""
            UPDATE orders
            SET payment_status = 'rejected',
                order_status = 'cancelled'
            WHERE id = ?
        """, (order_id,))

        conn.commit()
        conn.close()

        await query.message.reply_text(
            f"❌ تم رفض الدفع للطلب "
            f"#SAQ-{order_id:05d}"
        )

        try:

            await context.bot.send_message(
                chat_id=row["user_id"],
                text=f"""❌ تم رفض إثبات الدفع

🆔 الطلب:
#SAQ-{order_id:05d}

إذا كنت تعتقد أن هناك خطأ، تواصل مع الدعم."""
            )

        except Exception as e:
            print(
                "Reject notify error:",
                e
            )

        return

    # -----------------------------------------------------
    # MY ORDERS
    # -----------------------------------------------------

    if data == "my_orders":

        await show_my_orders(
            query,
            context
        )

        return

    # -----------------------------------------------------
    # SUPPORT
    # -----------------------------------------------------

    if data == "support":

        await query.message.reply_text(
            """🎧 الدعم الفني

للتواصل مع إدارة SaQR Agency:

📩 أرسل رسالتك هنا وسيتم تحويلها للإدارة."""
        )

        context.user_data[
            "support_mode"
        ] = True

        return


# =========================================================
# MY ORDERS
# =========================================================

async def show_my_orders(
    query,
    context
):

    user_id = query.from_user.id

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (
        user_id,
    )).fetchall()

    conn.close()

    if not rows:

        await query.message.reply_text(
            "📦 لا توجد طلبات حتى الآن.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    text = "📦 آخر طلباتك\n\n"

    for row in rows:

        text += (
            f"🆔 #SAQ-{row['id']:05d}\n"
            f"🛒 {row['service_name']}\n"
            f"📦 الكمية: {row['quantity']}\n"
            f"💰 {row['sale_price']:.2f} جنيه\n"
            f"⏳ {row['order_status']}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def message_handler(
    update,
    context
):

    user = update.effective_user

    # -----------------------------------------------------
    # SUPPORT
    # -----------------------------------------------------

    if context.user_data.get(
        "support_mode"
    ):

        text = update.message.text or ""

        context.user_data[
            "support_mode"
        ] = False

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""📩 رسالة دعم جديدة

👤 العميل:
{user.username or "بدون Username"}

🆔 Telegram ID:
{user.id}

━━━━━━━━━━━━━━

{text}"""
        )

        await update.message.reply_text(
            "✅ تم إرسال رسالتك للإدارة."
        )

        return

    # -----------------------------------------------------
    # PROGRAM LINK
    # -----------------------------------------------------

    if context.user_data.get(
        "waiting_program_link"
    ):

        order = context.user_data.get(
            "order"
        )

        if not order:
            return

        order["link"] = (
            update.message.text or ""
        )

        order["quantity"] = int(
            order.get(
                "quantity",
                1
            )
        )

        context.user_data[
            "waiting_program_link"
        ] = False

        await show_payment(
            update.message,
            context,
            order
        )

        return

    # -----------------------------------------------------
    # SOCIAL QUANTITY
    # -----------------------------------------------------

    order = context.user_data.get(
        "order"
    )

    if order and order.get(
        "provider"
    ) == "alkabos":

        if not context.user_data.get(
            "waiting_proof"
        ):

            try:

                quantity = int(
                    update.message.text
                )

            except Exception:

                await update.message.reply_text(
                    "❌ أرسل الكمية كرقم فقط."
                )

                return

            minimum = int(
                order["minimum"]
            )

            maximum = int(
                order["maximum"]
            )

            if quantity < minimum:

                await update.message.reply_text(
                    f"❌ الحد الأدنى هو {minimum}."
                )

                return

            if quantity > maximum:

                await update.message.reply_text(
                    f"❌ الحد الأقصى هو {maximum}."
                )

                return

            provider = find_alkabos_service(
                order["service_id"]
            )

            if not provider:

                await update.message.reply_text(
                    "❌ الخدمة لم تعد متاحة."
                )

                return

            rate = float(
                provider.get(
                    "rate",
                    0
                )
            )

            cost, sale, usd_egp = (
                await calculate_price(
                    rate,
                    quantity
                )
            )

            order["quantity"] = quantity
            order["cost"] = cost
            order["sale_price"] = sale

            await update.message.reply_text(
                f"""🧾 ملخص الطلب

🛒 الخدمة:
{order["service_name"]}

📦 الكمية:
{quantity}

💱 سعر الدولار:
{usd_egp:.2f} جنيه

💰 تكلفة الخدمة:
{cost:.2f} جنيه

💵 السعر النهائي:
{sale:.2f} جنيه

━━━━━━━━━━━━━━

🔗 أرسل رابط الحساب/المنشور الآن."""
            )

            context.user_data[
                "waiting_social_link"
            ] = True

            return

    # -----------------------------------------------------
    # SOCIAL LINK
    # -----------------------------------------------------

    if context.user_data.get(
        "waiting_social_link"
    ):

        order = context.user_data.get(
            "order"
        )

        if not order:
            return

        order["link"] = (
            update.message.text or ""
        )

        context.user_data[
            "waiting_social_link"
        ] = False

        await show_payment(
            update.message,
            context,
            order
        )

        return

    # -----------------------------------------------------
    # PROOF
    # -----------------------------------------------------

    if context.user_data.get(
        "waiting_proof"
    ):

        if not update.message.photo:

            await update.message.reply_text(
                "❌ أرسل صورة إثبات الدفع."
            )

            return

        order = context.user_data.get(
            "order"
        )

        if not order:

            await update.message.reply_text(
                "❌ لا يوجد طلب مفتوح."
            )

            return

        proof_file_id = (
            update.message.photo[-1].file_id
        )

        order_id = save_order(
            user,
            order,
            proof_file_id
        )

        context.user_data[
            "waiting_proof"
        ] = False

        await notify_admin(
            context,
            order_id
        )

        await update.message.reply_text(
            f"""✅ تم استلام إثبات الدفع

🆔 رقم الطلب:
#SAQ-{order_id:05d}

⏳ الحالة:
في انتظار مراجعة الإدارة."""
        )

        return

    await update.message.reply_text(
        "استخدم /start لفتح القائمة الرئيسية."
    )


# =========================================================
# START
# =========================================================

async def start(
    update,
    context
):

    context.user_data.clear()

    await update.message.reply_text(
        WELCOME,
        reply_markup=main_menu()
    )


# =========================================================
# COMMANDS
# =========================================================

async def balance(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ غير مصرح."
        )

        return

    result = await get_alkabos_balance()

    await update.message.reply_text(
        f"💰 Alkabos Balance\n\n"
        f"{result}"
    )


async def status(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ غير مصرح."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "الاستخدام:\n/status ORDER_ID"
        )

        return

    result = await get_alkabos_status(
        context.args[0]
    )

    await update.message.reply_text(
        f"📊 الحالة:\n\n{result}"
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update,
    context
):

    print(
        "BOT ERROR:",
        context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "balance",
            balance
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.PHOTO |
            filters.TEXT &
            ~filters.COMMAND,
            message_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print(
        "SaQR Agency Bot started."
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
