import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ✅ ЗАМІНИ НА СВІЙ ТОКЕН
BOT_TOKEN = "6132331328:AAEvOxiAopKLxrjdcEbe7Cta60FPuqK80Zw"

# ✅ ТВІЙ Telegram ID
ADMIN_ID = 6146918846

# Файл де зберігаються товари
DATA_FILE = "products.json"

# Стани для діалогу додавання товару
(ASK_CATEGORY, ASK_NAME, ASK_PRICE, ASK_CURRENCY, ASK_DESCRIPTION, ASK_PHOTO,
 ASK_NEW_CATEGORY, EDIT_CHOOSE, EDIT_FIELD, EDIT_VALUE) = range(10)

CURRENCIES = {
    "UAH": "🇺🇦 грн",
    "USD": "💵 USD",
    "EUR": "💶 EUR",
}

logging.basicConfig(level=logging.INFO)

# ============================================================
# 💾 Збереження / завантаження товарів
# ============================================================
def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Початкові категорії
    return {
        "🚲 Велосипеди": [],
        "📱 Електроніка": [],
        "🔧 Автозапчастини": []
    }

def save_products(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 🏠 /start — головне меню
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")]
        for cat in products.keys()
        if products[cat]  # показуємо тільки категорії з товарами
    ]
    keyboard.append([InlineKeyboardButton("📞 Зв'язатися з продавцем", callback_data="contact")])

    await update.message.reply_text(
        "👋 Вітаю! Це мій магазин.\n\nОберіть категорію товарів 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# 📂 Показати категорію
# ============================================================
async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.replace("cat_", "")
    products = load_products()
    items = products.get(cat, [])

    if not items:
        await query.edit_message_text("😔 В цій категорії поки немає товарів.")
        return

    keyboard = [
        [InlineKeyboardButton(
            f"{item['name']} — {item['price']} {CURRENCIES.get(item.get('currency', 'UAH'), '🇺🇦 грн')}",
            callback_data=f"item_{cat}_{i}"
        )]
        for i, item in enumerate(items)
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])

    await query.edit_message_text(
        f"{cat}\n\nОберіть товар:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# 📦 Показати товар
# ============================================================
async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, cat, idx = query.data.split("_", 2)
    products = load_products()
    item = products[cat][int(idx)]

    currency = CURRENCIES.get(item.get("currency", "UAH"), "🇺🇦 грн")
    text = (
        f"📦 *{item['name']}*\n\n"
        f"{item['description']}\n\n"
        f"💰 Ціна: *{item['price']} {currency}*"
    )

    keyboard = [
        [InlineKeyboardButton("🛒 Замовити", callback_data=f"order_{cat}_{idx}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"cat_{cat}")],
    ]

    if item.get("photo"):
        await query.message.delete()
        await query.message.chat.send_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============================================================
# 🛒 Замовлення
# ============================================================
async def order_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, cat, idx = query.data.split("_", 2)
    products = load_products()
    item = products[cat][int(idx)]
    user = query.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"

    currency = CURRENCIES.get(item.get("currency", "UAH"), "🇺🇦 грн")
    admin_text = (
        f"🛒 *Нове замовлення!*\n\n"
        f"Товар: {item['name']}\n"
        f"Ціна: {item['price']} {currency}\n\n"
        f"Покупець: {user.full_name}\n"
        f"Контакт: {username}"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Помилка надсилання адміну: {e}")

    reply_text = (
        f"✅ *Дякуємо за замовлення!*\n\n"
        f"Товар: {item['name']}\n"
        f"Ціна: {item['price']} {currency}\n\n"
        f"Продавець зв'яжеться з вами найближчим часом 🙌"
    )
    keyboard = [[InlineKeyboardButton("🏠 На головну", callback_data="back_main")]]

    try:
        await query.edit_message_caption(reply_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await query.edit_message_text(reply_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# 📞 Контакт
# ============================================================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📞 *Зв'язок з продавцем*\n\n"
        "Напишіть нам, і ми відповімо якнайшвидше!\n\n"
        "👤 @твій_username",  # ✅ ЗАМІНИ на свій username
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]])
    )

# ============================================================
# 🏠 Назад на головну
# ============================================================
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = load_products()
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")]
        for cat in products.keys()
        if products[cat]
    ]
    keyboard.append([InlineKeyboardButton("📞 Зв'язатися з продавцем", callback_data="contact")])

    try:
        await query.edit_message_text(
            "👋 Вітаю! Це мій магазин.\n\nОберіть категорію товарів 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.delete()
        await query.message.chat.send_message(
            "👋 Вітаю! Це мій магазин.\n\nОберіть категорію товарів 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============================================================
# 🔐 АДМІН ПАНЕЛЬ
# ============================================================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ У вас немає доступу.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Додати товар", callback_data="admin_add")],
        [InlineKeyboardButton("🗑 Видалити товар", callback_data="admin_delete")],
        [InlineKeyboardButton("➕ Додати категорію", callback_data="admin_add_cat")],
        [InlineKeyboardButton("🗑 Видалити категорію", callback_data="admin_del_cat")],
    ]
    await update.message.reply_text(
        "🔐 *Адмін панель*\n\nОберіть дію:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---- Додати товар: вибір категорії ----
async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = load_products()
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"addcat_{cat}")]
        for cat in products.keys()
    ]
    keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data="admin_cancel")])

    await query.edit_message_text(
        "Оберіть категорію для нового товару:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_CATEGORY

async def admin_choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.replace("addcat_", "")
    context.user_data["new_item"] = {"category": cat}

    await query.edit_message_text(f"Категорія: *{cat}*\n\nВведіть назву товару:", parse_mode="Markdown")
    return ASK_NAME

async def admin_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_item"]["name"] = update.message.text
    await update.message.reply_text("Введіть ціну (тільки число, наприклад: 5000):")
    return ASK_PRICE

async def admin_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
        context.user_data["new_item"]["price"] = price

        keyboard = [
            [InlineKeyboardButton("🇺🇦 Гривня (UAH)", callback_data="currency_UAH")],
            [InlineKeyboardButton("💵 Долар (USD)", callback_data="currency_USD")],
            [InlineKeyboardButton("💶 Євро (EUR)", callback_data="currency_EUR")],
        ]
        await update.message.reply_text(
            "Оберіть валюту:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ASK_CURRENCY
    except:
        await update.message.reply_text("⚠️ Введіть тільки число! Спробуйте ще раз:")
        return ASK_PRICE

async def admin_get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    currency = query.data.replace("currency_", "")
    context.user_data["new_item"]["currency"] = currency

    await query.edit_message_text("Введіть опис товару:")
    return ASK_DESCRIPTION

async def admin_get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_item"]["description"] = update.message.text
    await update.message.reply_text(
        "Надішліть фото товару або напишіть /skip щоб пропустити:"
    )
    return ASK_PHOTO

async def admin_get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = context.user_data["new_item"]

    if update.message.photo:
        item["photo"] = update.message.photo[-1].file_id
    else:
        item["photo"] = None

    # Зберігаємо товар
    products = load_products()
    cat = item.pop("category")
    products[cat].append(item)
    save_products(products)

    await update.message.reply_text(
        f"✅ Товар *{item['name']}* додано до категорії *{cat}*!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def admin_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = context.user_data["new_item"]
    item["photo"] = None

    products = load_products()
    cat = item.pop("category")
    products[cat].append(item)
    save_products(products)

    await update.message.reply_text(
        f"✅ Товар *{item['name']}* додано до категорії *{cat}*!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ---- Видалити товар ----
async def admin_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = load_products()
    keyboard = []
    for cat, items in products.items():
        for i, item in enumerate(items):
            keyboard.append([InlineKeyboardButton(
                f"🗑 {item['name']} ({cat})",
                callback_data=f"delitem_{cat}_{i}"
            )])
    keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data="admin_cancel")])

    if not keyboard[:-1]:
        await query.edit_message_text("😔 Немає товарів для видалення.")
        return

    await query.edit_message_text(
        "Оберіть товар для видалення:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, cat, idx = query.data.split("_", 2)
    products = load_products()
    item = products[cat].pop(int(idx))
    save_products(products)

    await query.edit_message_text(f"✅ Товар *{item['name']}* видалено!", parse_mode="Markdown")

# ---- Додати категорію ----
async def admin_add_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введіть назву нової категорії (можна з емодзі, наприклад: 🪑 Меблі):")
    return ASK_NEW_CATEGORY

async def admin_save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_name = update.message.text.strip()
    products = load_products()
    if cat_name in products:
        await update.message.reply_text("⚠️ Така категорія вже існує!")
    else:
        products[cat_name] = []
        save_products(products)
        await update.message.reply_text(f"✅ Категорію *{cat_name}* додано!", parse_mode="Markdown")
    return ConversationHandler.END

# ---- Видалити категорію ----
async def admin_del_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = load_products()
    keyboard = [
        [InlineKeyboardButton(f"🗑 {cat}", callback_data=f"delcat_{cat}")]
        for cat in products.keys()
    ]
    keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data="admin_cancel")])

    await query.edit_message_text(
        "Оберіть категорію для видалення:\n⚠️ Всі товари в ній також видаляться!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_confirm_del_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.replace("delcat_", "")
    products = load_products()
    del products[cat]
    save_products(products)

    await query.edit_message_text(f"✅ Категорію *{cat}* видалено!", parse_mode="Markdown")

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Скасовано.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Скасовано.")
    return ConversationHandler.END

# ============================================================
# 🚀 Запуск
# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Діалог додавання товару
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add, pattern="^admin_add$")],
        states={
            ASK_CATEGORY: [CallbackQueryHandler(admin_choose_category, pattern="^addcat_")],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_name)],
            ASK_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_price)],
            ASK_CURRENCY: [CallbackQueryHandler(admin_get_currency, pattern="^currency_")],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_description)],
            ASK_PHOTO: [
                MessageHandler(filters.PHOTO, admin_get_photo),
                CommandHandler("skip", admin_skip_photo),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$"),
            CommandHandler("cancel", cancel),
        ]
    )

    # Діалог додавання категорії
    cat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_cat, pattern="^admin_add_cat$")],
        states={
            ASK_NEW_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_category)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(add_conv)
    app.add_handler(cat_conv)
    app.add_handler(CallbackQueryHandler(admin_delete, pattern="^admin_delete$"))
    app.add_handler(CallbackQueryHandler(admin_confirm_delete, pattern="^delitem_"))
    app.add_handler(CallbackQueryHandler(admin_del_cat, pattern="^admin_del_cat$"))
    app.add_handler(CallbackQueryHandler(admin_confirm_del_cat, pattern="^delcat_"))
    app.add_handler(CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$"))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_item, pattern="^item_"))
    app.add_handler(CallbackQueryHandler(order_item, pattern="^order_"))
    app.add_handler(CallbackQueryHandler(contact, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))

    print("✅ Бот запущено!")
    app.run_polling()

if __name__ == "__main__":
    main()
