import os
import json
import sqlite3
import asyncio
import urllib.parse
import urllib.request
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# SaQR Agency
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ALKABOS_API_KEY = os.getenv("ALKABOS_API_KEY", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)

PAYMENT_NAME = os.getenv("PAYMENT_NAME", "Hosam Shaker").strip()
PAYMENT_METHOD = os.getenv("PAYMENT_METHOD", "Vodafone Cash").strip()
PAYMENT_NUMBER = os.getenv("PAYMENT_NUMBER", "").strip()

PROFIT_MARGIN = float(os.getenv("PROFIT_MARGIN", "70") or 70)

API_URL = "https://alkabos.com/api/v2"
DB_FILE = "saqr_orders.db"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")

if not ALKABOS_API_KEY:
    raise RuntimeError("ALKABOS_API_KEY is not set.")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID is not set.")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT DEFAULT '',
            service_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            service_type TEXT DEFAULT '',
            category TEXT DEFAULT '',
            link TEXT DEFAULT '',
            quantity INTEGER DEFAULT 0,
            extra TEXT DEFAULT '',
            cost REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'waiting',
            order_status TEXT DEFAULT 'waiting_payment',
            alkabos_order_id TEXT DEFAULT '',
            proof_file_id TEXT DEFAULT '',
            provider_status TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# ALKABOS API
# =========================================================

def alkabos_request(action, params=None):
    data = {
        "key": ALKABOS_API_KEY,
        "action": action,
    }

    if params:
        data.update(params)

    body = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SaQR-Agency-Bot/1.0",
        },
    )

    with urllib.request.urlopen(request, timeout=35) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)


async def api_request(action, params=None):
    return await asyncio.to_thread(
        alkabos_request,
        action,
        params
    )


SERVICES = []


async def refresh_services():
    global SERVICES

    try:
        result = await api_request("services")

        if isinstance(result, list):
            SERVICES = result
            print(f"Loaded {len(SERVICES)} services.")
            return SERVICES

        print("Invalid services response:", result)

    except Exception as error:
        print("Services API error:", repr(error))

    return SERVICES


async def add_alkabos_order(service, link, quantity, extra=""):
    service_type = str(
        service.get("type", "")
    ).lower()

    params = {
        "service": str(service["service"]),
        "link": link,
    }

    if quantity > 0:
        params["quantity"] = str(quantity)

    # Custom comments
    if "comment" in service_type and extra:
        params["comments"] = extra

    # Username-based services
    if "username" in service_type and extra:
        params["usernames"] = extra

    return await api_request("add", params)


async def get_alkabos_status(order_id):
    return await api_request(
        "status",
        {
            "order": str(order_id)
        }
    )


async def get_alkabos_balance():
    return await api_request("balance")


# =========================================================
# PRICING
# =========================================================

def calculate_price(service, quantity):
    rate = float(
        service.get("rate", 0) or 0
    )

    if quantity > 0:
        cost = rate * quantity / 1000
    else:
        cost = rate

    sale = cost * (
        1 + PROFIT_MARGIN / 100
    )

    return round(cost, 2), round(sale, 2)


def money(value):
    return f"{float(value):,.2f} جنيه"


# =========================================================
# DATABASE ORDER
# =========================================================

def create_order(user, data, proof_file_id):
    service = data["service"]

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO orders (
            user_id,
            username,
            service_id,
            service_name,
            service_type,
            category,
            link,
            quantity,
            extra,
            cost,
            sale_price,
            payment_status,
            order_status,
            alkabos_order_id,
            proof_file_id,
            provider_status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        str(service["service"]),
        service.get("name", "Service"),
        service.get("type", ""),
        service.get("category", ""),
        data.get("link", ""),
        int(data.get("quantity", 0)),
        data.get("extra", ""),
        float(data.get("cost", 0)),
        float(data.get("sale_price", 0)),
        "waiting",
        "waiting_payment",
        "",
        proof_file_id,
        "",
        datetime.now().isoformat(
            timespec="seconds"
        ),
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id


# =========================================================
# MAIN MENU
# =========================================================

WELCOME = """🦅 أهلاً بك في SaQR Agency

متجر الخدمات الرقمية

اختر ما تريد من القائمة 👇"""


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📱 جميع خدمات السوشيال ميديا",
                callback_data="categories:0"
            )
        ],
        [
            InlineKeyboardButton(
                "📦 طلباتي",
                callback_data="orders"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 الدعم",
                callback_data="support"
            )
        ],
    ])


# =========================================================
# CATEGORIES
# =========================================================

def get_categories():
    categories = []

    for service in SERVICES:

        category = str(
            service.get(
                "category",
                "خدمات أخرى"
            )
        ).strip()

        if category not in categories:
            categories.append(category)

    return categories


def category_keyboard(page=0):
    categories = get_categories()

    per_page = 8

    start = page * per_page
    end = start + per_page

    buttons = []

    for index in range(
        start,
        min(end, len(categories))
    ):

        name = categories[index]

        if len(name) > 45:
            name = name[:42] + "..."

        buttons.append([
            InlineKeyboardButton(
                f"📁 {name}",
                callback_data=f"category:{index}:0"
            )
        ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ السابق",
                callback_data=f"categories:{page - 1}"
            )
        )

    if end < len(categories):
        navigation.append(
            InlineKeyboardButton(
                "التالي ➡️",
                callback_data=f"categories:{page + 1}"
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# =========================================================
# SERVICES
# =========================================================

def get_category_services(category_index):
    categories = get_categories()

    if category_index >= len(categories):
        return None, []

    category = categories[category_index]

    services = [
        service
        for service in SERVICES
        if str(
            service.get(
                "category",
                "خدمات أخرى"
            )
        ).strip() == category
    ]

    return category, services


def services_keyboard(
    category_index,
    page=0
):

    category, services = get_category_services(
        category_index
    )

    if category is None:
        return category_keyboard()

    per_page = 8

    start = page * per_page
    end = start + per_page

    buttons = []

    for service in services[start:end]:

        service_id = str(
            service.get("service")
        )

        name = str(
            service.get(
                "name",
                f"Service {service_id}"
            )
        )

        if len(name) > 45:
            name = name[:42] + "..."

        buttons.append([
            InlineKeyboardButton(
                f"🛒 {name}",
                callback_data=f"service:{service_id}"
            )
        ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ السابق",
                callback_data=(
                    f"category:{category_index}:{page - 1}"
                )
            )
        )

    if end < len(services):
        navigation.append(
            InlineKeyboardButton(
                "التالي ➡️",
                callback_data=(
                    f"category:{category_index}:{page + 1}"
                )
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton(
            "🔙 الأقسام",
            callback_data="categories:0"
        )
    ])

    return InlineKeyboardMarkup(buttons)


def find_service(service_id):

    for service in SERVICES:

        if str(
            service.get("service")
        ) == str(service_id):

            return service

    return None


# =========================================================
# SERVICE DETAILS
# =========================================================

def service_details(service):

    name = service.get(
        "name",
        "خدمة"
    )

    service_id = service.get(
        "service",
        "-"
    )

    category = service.get(
        "category",
        "خدمات أخرى"
    )

    service_type = service.get(
        "type",
        "Default"
    )

    rate = service.get(
        "rate",
        "0"
    )

    minimum = service.get(
        "min",
        "-"
    )

    maximum = service.get(
        "max",
        "-"
    )

    refill = (
        "متاح"
        if service.get("refill")
        else "غير متاح"
    )

    cancel = (
        "متاح"
        if service.get("cancel")
        else "غير متاح"
    )

    return f"""🛒 {name}

📁 القسم:
{category}

🆔 رقم الخدمة:
{service_id}

⚙️ النوع:
{service_type}

💰 سعر التكلفة:
{rate} لكل 1000

📦 الحد الأدنى:
{minimum}

📦 الحد الأقصى:
{maximum}

🔄 Refill:
{refill}

❌ Cancel:
{cancel}

📈 هامش SaQR:
{PROFIT_MARGIN:.0f}%

اختر ما تريد 👇"""


def service_buttons(service_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 شراء الخدمة",
                callback_data=f"buy:{service_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 رجوع",
                callback_data="categories:0"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 الرئيسية",
                callback_data="home"
            )
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        WELCOME,
        reply_markup=main_menu()
    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    # HOME
    if data == "home":

        context.user_data.clear()

        await query.message.reply_text(
            WELCOME,
            reply_markup=main_menu()
        )

        return

    # CATEGORIES
    if data.startswith("categories:"):

        page = int(
            data.split(":")[1]
        )

        if not SERVICES:
            await refresh_services()

        if not SERVICES:

            await query.message.reply_text(
                "❌ تعذر تحميل الخدمات من الكابوس حاليًا."
            )

            return

        await query.message.reply_text(
            "📁 اختر القسم:",
            reply_markup=category_keyboard(page)
        )

        return

    # CATEGORY
    if data.startswith("category:"):

        _, category_index, page = data.split(":")

        category_index = int(category_index)
        page = int(page)

        category, services = get_category_services(
            category_index
        )

        if category is None:

            await query.message.reply_text(
                "❌ القسم غير موجود."
            )

            return

        await query.message.reply_text(
            f"""📁 {category}

اختر الخدمة المطلوبة:""",
            reply_markup=services_keyboard(
                category_index,
                page
            )
        )

        return

    # SERVICE
    if data.startswith("service:"):

        service_id = data.split(
            ":",
            1
        )[1]

        service = find_service(
            service_id
        )

        if not service:

            await query.message.reply_text(
                "❌ الخدمة غير موجودة."
            )

            return

        await query.message.reply_text(
            service_details(service),
            reply_markup=service_buttons(
                service_id
            )
        )

        return

    # BUY
    if data.startswith("buy:"):

        service_id = data.split(
            ":",
            1
        )[1]

        service = find_service(
            service_id
        )

        if not service:

            await query.message.reply_text(
                "❌ الخدمة غير موجودة."
            )

            return

        context.user_data["order"] = {
            "service": service,
            "quantity": 0,
            "link": "",
            "extra": "",
            "cost": 0,
            "sale_price": 0,
        }

        service_type = str(
            service.get(
                "type",
                ""
            )
        ).lower()

        # CUSTOM COMMENTS
        if "custom comments" in service_type:

            context.user_data["stage"] = "comments"

            await query.message.reply_text(
                """💬 أرسل التعليقات المطلوبة.

اكتب كل تعليق في سطر منفصل."""
            )

            return

        # NORMAL QUANTITY SERVICE
        if (
            service.get("min") is not None
            and service.get("max") is not None
        ):

            context.user_data["stage"] = "quantity"

            await query.message.reply_text(
                f"""📦 أرسل الكمية المطلوبة.

الحد الأدنى:
{service.get("min")}

الحد الأقصى:
{service.get("max")}

مثال:
1000"""
            )

            return

        # PACKAGE SERVICE
        context.user_data["stage"] = "link"

        await query.message.reply_text(
            "🔗 أرسل الرابط المطلوب تنفيذ الخدمة عليه."
        )

        return

    # GO TO PAYMENT
    if data == "go_payment":

        await show_payment(
            query,
            context
        )

        return

    # PAYMENT SENT
    if data == "payment_sent":

        order = context.user_data.get(
            "order"
        )

        if not order:

            await query.message.reply_text(
                "❌ لا يوجد طلب مفتوح."
            )

            return

        context.user_data["stage"] = "proof"

        await query.message.reply_text(
            """🧾 إثبات الدفع

أرسل الآن صورة واضحة لإيصال التحويل."""
        )

        return

    # APPROVE
    if data.startswith("approve:"):

        order_id = int(
            data.split(":")[1]
        )

        await approve_order(
            query,
            context,
            order_id
        )

        return

    # REJECT
    if data.startswith("reject:"):

        order_id = int(
            data.split(":")[1]
        )

        await reject_order(
            query,
            context,
            order_id
        )

        return

    # ORDERS
    if data == "orders":

        await show_orders(
            query
        )

        return

    # STATUS
    if data.startswith("status:"):

        order_id = int(
            data.split(":")[1]
        )

        await show_order_status(
            query,
            order_id
        )

        return

    # SUPPORT
    if data == "support":

        await query.message.reply_text(
            """📞 دعم SaQR Agency

إذا عندك مشكلة في طلب:

🆔 أرسل رقم الطلب
📝 اشرح المشكلة
📷 أرفق صورة إذا لزم الأمر

وسيتم مراجعة طلبك."""
        )

        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    stage = context.user_data.get(
        "stage"
    )

    order = context.user_data.get(
        "order"
    )

    if not order or not stage:

        await update.message.reply_text(
            "استخدم /start لفتح القائمة."
        )

        return

    service = order["service"]

    # QUANTITY
    if stage == "quantity":

        value = update.message.text.strip()

        value = value.replace(
            ",",
            ""
        )

        try:

            quantity = int(value)

        except ValueError:

            await update.message.reply_text(
                "❌ أرسل الكمية كرقم فقط."
            )

            return

        minimum = int(
            float(
                service.get(
                    "min",
                    1
                )
            )
        )

        maximum = int(
            float(
                service.get(
                    "max",
                    999999999
                )
            )
        )

        if quantity < minimum or quantity > maximum:

            await update.message.reply_text(
                f"""❌ الكمية غير صحيحة.

الحد الأدنى:
{minimum}

الحد الأقصى:
{maximum}"""
            )

            return

        cost, sale_price = calculate_price(
            service,
            quantity
        )

        order["quantity"] = quantity
        order["cost"] = cost
        order["sale_price"] = sale_price

        context.user_data["stage"] = "link"

        await update.message.reply_text(
            f"""📦 الكمية:
{quantity}

💰 السعر:
{money(sale_price)}

🔗 الآن أرسل رابط الحساب أو المنشور."""
        )

        return

    # COMMENTS
    if stage == "comments":

        comments = update.message.text.strip()

        lines = [
            line.strip()
            for line in comments.splitlines()
            if line.strip()
        ]

        if not lines:

            await update.message.reply_text(
                "❌ أرسل التعليقات المطلوبة."
            )

            return

        quantity = len(lines)

        minimum = int(
            float(
                service.get(
                    "min",
                    1
                )
            )
        )

        maximum = int(
            float(
                service.get(
                    "max",
                    999999999
                )
            )
        )

        if quantity < minimum or quantity > maximum:

            await update.message.reply_text(
                f"""❌ عدد التعليقات يجب أن يكون بين:

{minimum}

و

{maximum}"""
            )

            return

        cost, sale_price = calculate_price(
            service,
            quantity
        )

        order["quantity"] = quantity
        order["cost"] = cost
        order["sale_price"] = sale_price
        order["extra"] = "\n".join(lines)

        context.user_data["stage"] = "link"

        await update.message.reply_text(
            f"""💬 عدد التعليقات:
{quantity}

💰 السعر:
{money(sale_price)}

🔗 أرسل رابط المنشور."""
        )

        return

    # LINK
    if stage == "link":

        link = update.message.text.strip()

        if not (
            link.startswith("http://")
            or link.startswith("https://")
        ):

            await update.message.reply_text(
                "❌ أرسل رابطًا صحيحًا يبدأ بـ http أو https."
            )

            return

        order["link"] = link

        if order["quantity"] == 0:

            cost, sale_price = calculate_price(
                service,
                0
            )

            order["cost"] = cost
            order["sale_price"] = sale_price

        context.user_data["stage"] = "confirm"

        await show_review(
            update.message,
            order
        )

        return

    # PAYMENT
    if stage == "payment":

        await update.message.reply_text(
            "اضغط «أرسلت التحويل» ثم أرسل صورة الإيصال."
        )

        return

    # PROOF
    if stage == "proof":

        await update.message.reply_text(
            "🧾 أرسل صورة إيصال التحويل."
        )

        return


# =========================================================
# ORDER REVIEW
# =========================================================

async def show_review(
    message,
    order
):

    service = order["service"]

    text = f"""🧾 مراجعة الطلب

🛒 الخدمة:
{service.get("name", "Service")}

🆔 رقم الخدمة:
{service.get("service")}

📦 الكمية:
{order["quantity"] or "حسب الخدمة"}

🔗 الرابط:
{order["link"]}

💰 الإجمالي:
{money(order["sale_price"])}

━━━━━━━━━━━━━━

هل تريد الانتقال للدفع؟"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💳 متابعة للدفع",
                callback_data="go_payment"
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
# PAYMENT
# =========================================================

async def show_payment(
    query,
    context
):

    order = context.user_data.get(
        "order"
    )

    if not order:

        await query.message.reply_text(
            "❌ انتهت جلسة الطلب."
        )

        return

    context.user_data["stage"] = "payment"

    text = f"""💳 الدفع

🛒 الخدمة:
{order["service"].get("name", "Service")}

📦 الكمية:
{order["quantity"] or "حسب الخدمة"}

💰 المبلغ المطلوب:
{money(order["sale_price"])}

━━━━━━━━━━━━━━

طريقة الدفع:
{PAYMENT_METHOD}

اسم المستلم:
{PAYMENT_NAME}

رقم التحويل:
{PAYMENT_NUMBER}

━━━━━━━━━━━━━━

1️⃣ حوّل المبلغ بالكامل.
2️⃣ احتفظ بالإيصال.
3️⃣ اضغط «أرسلت التحويل».
4️⃣ أرسل صورة الإيصال.

⚠️ لن يتم تنفيذ الطلب قبل مراجعة الدفع."""

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

    await query.message.reply_text(
        text,
        reply_markup=keyboard
    )


# =========================================================
# PAYMENT PROOF
# =========================================================

async def photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if context.user_data.get(
        "stage"
    ) != "proof":

        await update.message.reply_text(
            "استخدم /start لبدء طلب."
        )

        return

    order = context.user_data.get(
        "order"
    )

    if not order:

        await update.message.reply_text(
            "❌ لا يوجد طلب."
        )

        return

    photo = update.message.photo[-1]

    local_order_id = create_order(
        update.effective_user,
        order,
        photo.file_id
    )

    context.user_data.clear()

    await update.message.reply_text(
        f"""✅ تم استلام إثبات الدفع

🆔 رقم طلب SaQR:
#SAQ-{local_order_id:05d}

📌 الحالة:
في انتظار مراجعة الدفع

سيتم إشعارك بعد المراجعة."""
    )

    await notify_admin(
        update,
        local_order_id
    )


# =========================================================
# ADMIN NOTIFICATION
# =========================================================

async def notify_admin(
    update,
    order_id
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    conn.close()

    if not row:
        return

    username = (
        f"@{row['username']}"
        if row["username"]
        else "بدون Username"
    )

    text = f"""🔔 طلب دفع جديد

🆔 رقم SaQR:
#SAQ-{row["id"]:05d}

👤 العميل:
{username}

🆔 Telegram ID:
{row["user_id"]}

━━━━━━━━━━━━━━

🛒 الخدمة:
{row["service_name"]}

🆔 رقم الخدمة:
{row["service_id"]}

📦 الكمية:
{row["quantity"] or "حسب الخدمة"}

🔗 الرابط:
{row["link"]}

💰 التكلفة:
{money(row["cost"])}

💵 سعر البيع:
{money(row["sale_price"])}

📈 الربح:
{PROFIT_MARGIN:.0f}%

━━━━━━━━━━━━━━

📌 الدفع:
في انتظار المراجعة"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ تأكيد الدفع وتنفيذ",
                callback_data=f"approve:{row['id']}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ رفض الدفع",
                callback_data=f"reject:{row['id']}"
            )
        ],
    ])

    await update.get_bot().send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=keyboard
    )

    if row["proof_file_id"]:

        await update.get_bot().send_photo(
            chat_id=ADMIN_ID,
            photo=row["proof_file_id"],
            caption=(
                f"🧾 إثبات الدفع "
                f"#SAQ-{row['id']:05d}"
            )
        )


# =========================================================
# ADMIN APPROVE
# =========================================================

async def approve_order(
    query,
    context,
    local_id
):

    if query.from_user.id != ADMIN_ID:

        await query.message.reply_text(
            "❌ غير مصرح."
        )

        return

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (local_id,)
    ).fetchone()

    conn.close()

    if not row:

        await query.message.reply_text(
            "❌ الطلب غير موجود."
        )

        return

    if row["payment_status"] == "approved":

        await query.message.reply_text(
            "⚠️ الطلب تم اعتماده بالفعل."
        )

        return

    service = find_service(
        row["service_id"]
    )

    if not service:

        await query.message.reply_text(
            "❌ الخدمة لم تعد موجودة في قائمة الكابوس."
        )

        return

    conn = get_db()

    conn.execute(
        """
        UPDATE orders
        SET payment_status = 'approved',
            order_status = 'sending'
        WHERE id = ?
        """,
        (local_id,)
    )

    conn.commit()
    conn.close()

    try:

        result = await add_alkabos_order(
            service,
            row["link"],
            row["quantity"],
            row["extra"]
        )

    except Exception as error:

        conn = get_db()

        conn.execute(
            """
            UPDATE orders
            SET order_status = 'provider_error'
            WHERE id = ?
            """,
            (local_id,)
        )

        conn.commit()
        conn.close()

        await query.message.reply_text(
            f"""❌ حدث خطأ أثناء إرسال الطلب للكابوس:

{error}

لم يتم إرسال الطلب بنجاح."""
        )

        return

    if not isinstance(result, dict) or not result.get("order"):

        conn = get_db()

        conn.execute(
            """
            UPDATE orders
            SET order_status = 'provider_error',
                provider_status = ?
            WHERE id = ?
            """,
            (
                json.dumps(
                    result,
                    ensure_ascii=False
                ),
                local_id
            )
        )

        conn.commit()
        conn.close()

        await query.message.reply_text(
            "❌ الكابوس رفض الطلب:\n\n"
            + json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return

    provider_order_id = str(
        result["order"]
    )

    conn = get_db()

    conn.execute(
        """
        UPDATE orders
        SET order_status = 'processing',
            alkabos_order_id = ?
        WHERE id = ?
        """,
        (
            provider_order_id,
            local_id
        )
    )

    conn.commit()
    conn.close()

    await query.message.reply_text(
        f"""✅ تم تنفيذ الطلب

🆔 SaQR:
#SAQ-{local_id:05d}

🆔 رقم الكابوس:
{provider_order_id}

📦 الحالة:
جاري التنفيذ"""
    )

    await context.bot.send_message(
        chat_id=row["user_id"],
        text=f"""✅ تم تأكيد طلبك

🆔 رقم الطلب:
#SAQ-{local_id:05d}

🛒 الخدمة:
{row["service_name"]}

📦 الكمية:
{row["quantity"] or "حسب الخدمة"}

💰 المبلغ:
{money(row["sale_price"])}

🆔 رقم الكابوس:
{provider_order_id}

📌 الحالة:
جاري التنفيذ""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 متابعة الحالة",
                    callback_data=f"status:{local_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ],
        ])
    )


# =========================================================
# ADMIN REJECT
# =========================================================

async def reject_order(
    query,
    context,
    local_id
):

    if query.from_user.id != ADMIN_ID:

        await query.message.reply_text(
            "❌ غير مصرح."
        )

        return

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (local_id,)
    ).fetchone()

    if not row:

        conn.close()

        await query.message.reply_text(
            "❌ الطلب غير موجود."
        )

        return

    conn.execute(
        """
        UPDATE orders
        SET payment_status = 'rejected',
            order_status = 'payment_rejected'
        WHERE id = ?
        """,
        (local_id,)
    )

    conn.commit()
    conn.close()

    await query.message.reply_text(
        f"❌ تم رفض الدفع للطلب #SAQ-{local_id:05d}"
    )

    await context.bot.send_message(
        chat_id=row["user_id"],
        text=f"""❌ لم يتم اعتماد إثبات الدفع

🆔 رقم الطلب:
#SAQ-{local_id:05d}

إذا كنت تعتقد أن هناك خطأ، تواصل مع الدعم."""
    )


# =========================================================
# CUSTOMER ORDERS
# =========================================================

async def show_orders(
    query
):

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (query.from_user.id,)
    ).fetchall()

    conn.close()

    if not rows:

        await query.message.reply_text(
            "📦 لا توجد طلبات حتى الآن.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛒 تصفح الخدمات",
                        callback_data="categories:0"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ],
            ])
        )

        return

    text = "📦 آخر طلباتك:\n\n"

    buttons = []

    for row in rows:

        text += f"""🆔 #SAQ-{row["id"]:05d}
🛒 {row["service_name"]}
📦 {row["quantity"] or "حسب الخدمة"}
💰 {money(row["sale_price"])}
📌 {row["order_status"]}

"""

        if row["alkabos_order_id"]:

            buttons.append([
                InlineKeyboardButton(
                    f"🔄 #SAQ-{row['id']:05d}",
                    callback_data=(
                        f"status:{row['id']}"
                    )
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            "🏠 الرئيسية",
            callback_data="home"
        )
    ])

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# =========================================================
# ORDER STATUS
# =========================================================

async def show_order_status(
    query,
    local_id
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
        """,
        (
            local_id,
            query.from_user.id
        )
    ).fetchone()

    conn.close()

    if not row:

        await query.message.reply_text(
            "❌ الطلب غير موجود."
        )

        return

    if not row["alkabos_order_id"]:

        await query.message.reply_text(
            f"""🆔 #SAQ-{local_id:05d}

📌 الحالة:
{row["order_status"]}

لم يتم إرسال الطلب للمزود بعد."""
        )

        return

    try:

        result = await get_alkabos_status(
            row["alkabos_order_id"]
        )

    except Exception as error:

        await query.message.reply_text(
            f"""❌ تعذر تحديث الحالة حاليًا:

{error}"""
        )

        return

    status = str(
        result.get(
            "status",
            "Unknown"
        )
    )

    remains = result.get(
        "remains",
        "-"
    )

    start_count = result.get(
        "start_count",
        "-"
    )

    conn = get_db()

    conn.execute(
        """
        UPDATE orders
        SET provider_status = ?,
            order_status = ?
        WHERE id = ?
        """,
        (
            status,
            status,
            local_id
        )
    )

    conn.commit()
    conn.close()

    await query.message.reply_text(
        f"""📦 حالة الطلب

🆔 SaQR:
#SAQ-{local_id:05d}

🆔 رقم الكابوس:
{row["alkabos_order_id"]}

🛒 الخدمة:
{row["service_name"]}

📌 الحالة:
{status}

📊 البداية:
{start_count}

📉 المتبقي:
{remains}""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 تحديث",
                    callback_data=f"status:{local_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 طلباتي",
                    callback_data="orders"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ],
        ])
    )


# =========================================================
# ADMIN COMMANDS
# =========================================================

async def refresh_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ غير مصرح."
        )

        return

    services = await refresh_services()

    await update.message.reply_text(
        f"""✅ تم تحديث الخدمات

📦 عدد الخدمات:
{len(services)}"""
    )


async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ غير مصرح."
        )

        return

    try:

        balance = await get_alkabos_balance()

        await update.message.reply_text(
            "💰 رصيد الكابوس:\n\n"
            + json.dumps(
                balance,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as error:

        await update.message.reply_text(
            f"❌ تعذر قراءة الرصيد:\n{error}"
        )


# =========================================================
# ERROR
# =========================================================

async def error_handler(
    update,
    context
):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# =========================================================
# STARTUP
# =========================================================

async def post_init(
    application
):

    init_db()

    services = await refresh_services()

    print(
        "SaQR Agency started."
    )

    print(
        f"Services loaded: {len(services)}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
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
            "refresh",
            refresh_command
        )
    )

    application.add_handler(
        CommandHandler(
            "balance",
            balance_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print(
        "SaQR Agency bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
