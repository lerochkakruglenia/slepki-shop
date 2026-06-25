import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import CLIENT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)


# ===== КЛАВИАТУРЫ =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛍 О магазине", callback_data="about")],
        [InlineKeyboardButton("📦 Заказать", callback_data="order")],
        [InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")],
        [InlineKeyboardButton("📊 Мой заказ", callback_data="my_order")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])


def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back")]])


def product_menu():
    keyboard = [
        [InlineKeyboardButton("👫 Парные брелочки", callback_data="product_couple")],
        [InlineKeyboardButton("🧸 Игрушка", callback_data="product_toy")],
        [InlineKeyboardButton("❤️ Брелок-сердечко", callback_data="product_heart")],
        [InlineKeyboardButton("◀️ Назад", callback_data="order_back_phone")],
    ]
    return InlineKeyboardMarkup(keyboard)


def delivery_menu():
    keyboard = [
        [InlineKeyboardButton("🚚 СДЭК", callback_data="delivery_sdek")],
        [InlineKeyboardButton("📮 Гос. почта", callback_data="delivery_post")],
        [InlineKeyboardButton("🏠 Самовывоз (Минск)", callback_data="delivery_pickup")],
        [InlineKeyboardButton("◀️ Назад", callback_data="order_back_product")],
    ]
    return InlineKeyboardMarkup(keyboard)


def rating_menu():
    keyboard = [
        [InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_5")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_4")],
        [InlineKeyboardButton("⭐⭐⭐", callback_data="rating_3")],
        [InlineKeyboardButton("⭐⭐", callback_data="rating_2")],
        [InlineKeyboardButton("⭐", callback_data="rating_1")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===== СОСТОЯНИЯ =====
(PHONE, PRODUCT, DESC, DELIVERY, ADDR, CONFIRM) = range(6)
(REVIEW_TEXT, REVIEW_RATING) = range(10, 12)

temp = {}


# ===== ОБРАБОТЧИКИ =====
async def start(update, context):
    await update.message.reply_text(
        f"🌷аминка лепит\n\n"
        f"Привет, {update.effective_user.first_name}!\n"
        f"Я делаю брелочки из полимерной глины и меха на заказ ❤️\n\n"
        f"Каждый малыш создается с душой!",
        reply_markup=main_menu()
    )


async def about(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🛍 О магазине\n\n"
        "👋 Меня зовут Амина\n\n"
        "Я создаю уникальные брелочки из полимерной глины и меха. "
        "Каждый из них особенный и не похож на другие.\n\n"
        "💰 Цены:\n"
        "• Парные брелочки: 150 BYN\n"
        "• Игрушка: 140 BYN (3800₽)\n"
        "• Брелок-сердечко: 80-90 BYN (2100-2500₽)\n\n"
        "🚚 Доставка:\n"
        "• СДЭК (~550-800₽ в зависимости от региона)\n"
        "• Гос. почта\n"
        "• Самовывоз из Минска\n\n"
        "💳 Оплата на карту после показа процесса работы\n\n"
        "📱 Контакты:\n"
        "• Telegram: @cblrokxx\n"
        "• Канал: t.me/slep_ki\n\n"
        "🌐 Соц сети:\n"
        "• TikTok: https://www.tiktok.com/@aminalepit\n"
        "• Instagram: https://www.instagram.com/amene.relique\n"
        "• VK: https://vk.ru/slep_ki",
        reply_markup=back_button()
    )


# ===== ОТЗЫВЫ =====
async def reviews(update, context):
    query = update.callback_query
    await query.answer()

    reviews_list = db.get_approved_reviews()

    if not reviews_list:
        text = "⭐ Отзывы\n\nПока нет отзывов. Будь первой!"
    else:
        text = "⭐ Отзывы\n\n"
        for r in reviews_list:
            text += f"{'⭐' * r['rating']} {r['client_name']}:\n"
            text += f"{r['text']}\n"
            text += f"📅 {r['created_at'][:10]}\n\n"

    keyboard = [
        [InlineKeyboardButton("✍️ Оставить отзыв", callback_data="review_start")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def review_start(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "✍️ Оставь отзыв\n\n"
        "Напиши свой отзыв о моей работе ❤️",
        reply_markup=back_button()
    )
    return REVIEW_TEXT


async def review_get_text(update, context):
    user_id = str(update.effective_user.id)
    temp[user_id] = {'text': update.message.text}

    await update.message.reply_text(
        "⭐ Оцени работу\n\n"
        "Выбери количество звездочек:",
        reply_markup=rating_menu()
    )
    return REVIEW_RATING


async def review_get_rating(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    rating = int(query.data.split('_')[1])

    temp[user_id]['rating'] = rating
    data = temp[user_id]
    user = update.effective_user

    db.create_review({
        'client_name': user.first_name or 'Клиент',
        'client_telegram_id': str(user.id),
        'text': data['text'],
        'rating': data['rating'],
        'is_approved': False
    })

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"✍️ Новый отзыв!\n\n"
                f"👤 Клиент: {user.first_name or 'Клиент'}\n"
                f"⭐ Оценка: {data['rating']}/5\n"
                f"📝 Текст: {data['text'][:100]}...\n\n"
                f"⏳ Отзыв ожидает модерации."
            )
        except:
            pass

    await query.edit_message_text(
        "✅ Спасибо за отзыв!\n\n"
        "Он будет опубликован после проверки 🤍",
        reply_markup=main_menu()
    )

    del temp[user_id]
    return ConversationHandler.END


# ===== МОЙ ЗАКАЗ =====
async def my_order(update, context):
    query = update.callback_query
    await query.answer()

    orders = db.get_orders_by_user(update.effective_user.id)

    if not orders:
        await query.edit_message_text(
            "📊 Мои заказы\n\nУ тебя пока нет заказов 😔",
            reply_markup=back_button()
        )
        return

    text = "📊 Мои заказы\n\n"

    for order in orders:
        product_names = {
            'couple': 'парные брелочки',
            'toy': 'игрушка',
            'heart': 'брелок-сердечко'
        }

        status_names = {
            'new': '🆕 Новый (ожидает обработки)',
            'processing': '🔄 В обработке',
            'ready': '✅ Готов к отправке',
            'shipped': '🚚 Отправлен',
            'completed': '🏁 Выполнен',
            'cancelled': '❌ Отменен'
        }

        text += f"📋 Номер заказа: {order['order_number']}\n"
        text += f"🧸 Тип: {product_names.get(order['product_type'], order['product_type'])}\n"
        text += f"📊 Статус: {status_names.get(order['status'], order['status'])}\n"
        text += f"📅 Дата: {order['created_at'][:10]}\n"

        if order.get('completion_date'):
            text += f"📆 Готовность: {order['completion_date']}\n"

        text += "\n"

    await query.edit_message_text(
        text,
        reply_markup=back_button()
    )


# ===== ОФОРМЛЕНИЕ ЗАКАЗА =====
async def start_order(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    user = update.effective_user

    # Сохраняем имя из Telegram
    temp[user_id] = {
        'name': user.first_name or 'Клиент',
        'username': user.username
    }

    await query.edit_message_text(
        "📦 Оформление заказа\n\n"
        f"👤 Имя: {temp[user_id]['name']}\n\n"
        "📱 Напиши номер телефона для связи:\n"
        "📌 Пример: +375 29 1234567",
        reply_markup=back_button()
    )
    return PHONE


async def get_phone(update, context):
    user_id = str(update.effective_user.id)
    temp[user_id]['phone'] = update.message.text

    await update.message.reply_text(
        "🧸 Что заказываем?",
        reply_markup=product_menu()
    )
    return PRODUCT


async def get_product(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)

    product_map = {
        'product_couple': ('couple', 'парные брелочки', '150 BYN'),
        'product_toy': ('toy', 'игрушка', '140 BYN (3800₽)'),
        'product_heart': ('heart', 'брелок-сердечко', '80-90 BYN (2100-2500₽)')
    }

    if query.data in product_map:
        product_type, product_name, price = product_map[query.data]
        temp[user_id]['product_type'] = product_type
        temp[user_id]['product_name'] = product_name
        temp[user_id]['price'] = price

    await query.edit_message_text(
        f"📝 Опиши свой заказ\n\n"
        f"💰 Цена: {temp[user_id]['price']}\n\n"
        "Расскажи подробнее:\n"
        "• Какой цвет?\n"
        "• Какая внешность?\n"
        "• Особенности?\n"
        "• Ссылка на мудборд (если есть)\n\n"
        "💡 Чем подробнее, тем лучше получится ❤️",
        reply_markup=back_button()
    )
    return DESC


async def get_desc(update, context):
    user_id = str(update.effective_user.id)
    temp[user_id]['desc'] = update.message.text

    await update.message.reply_text(
        "🚚 Выбери способ доставки",
        reply_markup=delivery_menu()
    )
    return DELIVERY


async def get_delivery(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    method = query.data.split('_')[1]

    if method == 'pickup':
        temp[user_id]['delivery'] = '🏠 Самовывоз (Минск)'
        temp[user_id]['delivery_method'] = 'pickup'
        temp[user_id]['address'] = 'Самовывоз из Минска'

        return await confirm_order_from_callback(update, context)

    temp[user_id]['delivery_method'] = method

    if method == 'sdek':
        temp[user_id]['delivery'] = '🚚 СДЭК'
        text = (
            "🚚 СДЭК\n\n"
            "Напиши адрес доставки:\n"
            "📍 Город, улица, дом, квартира\n\n"
            "💸 Примерная стоимость доставки:\n"
            "• Москва, Питер: ~550-600₽\n"
            "• Казань, Екатеринбург: ~600-700₽\n"
            "• Новосибирск, Астана: ~700-800₽\n"
            "• Норильск: ~1600-1700₽"
        )
    else:
        temp[user_id]['delivery'] = '📮 Гос. почта'
        text = (
            "📮 Гос. почта\n\n"
            "Напиши полный почтовый адрес:\n"
            "📌 Индекс, город, улица, дом, квартира"
        )

    await query.edit_message_text(
        text,
        reply_markup=back_button()
    )
    return ADDR


async def get_address(update, context):
    user_id = str(update.effective_user.id)
    temp[user_id]['address'] = update.message.text
    return await confirm_order(update, context)


async def confirm_order_from_callback(update, context):
    """Подтверждение заказа для самовывоза (из callback)"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    data = temp[user_id]

    text = (
        "📋 Проверь данные заказа\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🧸 Тип: {data['product_name']}\n"
        f"💰 Цена (ориентировачная): {data['price']}\n\n"
        f"📝 Описание:\n{data['desc'][:150]}{'...' if len(data['desc']) > 150 else ''}\n\n"
        f"🚚 Доставка: {data['delivery']}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "🏠 Я свяжусь с вами для выбора удобного адреса 📍\n\n"
        "✅ Все верно?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад к доставке", callback_data="order_back_delivery")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back")],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM


async def confirm_order(update, context):
    """Подтверждение заказа (из сообщения)"""
    user_id = str(update.effective_user.id)
    data = temp[user_id]

    text = (
        "📋 Проверь данные заказа\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🧸 Тип: {data['product_name']}\n"
        f"💰 Цена (ориентировачная): {data['price']}\n\n"
        f"📝 Описание:\n{data['desc'][:150]}{'...' if len(data['desc']) > 150 else ''}\n\n"
        f"🚚 Доставка: {data['delivery']}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "✅ Все верно?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад к доставке", callback_data="order_back_delivery")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM


async def order_confirm(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    data = temp[user_id]
    user = update.effective_user

    order = db.create_order({
        'client_name': data['name'],
        'client_phone': data['phone'],
        'client_telegram_id': str(user.id),
        'client_username': data.get('username'),
        'product_type': data['product_type'],
        'description': data['desc'],
        'delivery_method': data['delivery_method'],
        'delivery_address': data['address'],
        'status': 'new'
    })

    admin_text = (
        f"🆕 Новый заказ!\n\n"
        f"📋 Номер: {order['order_number']}\n"
        f"👤 Клиент: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🔹 Telegram: @{data.get('username', 'Не указан')}\n"
        f"🧸 Тип: {data['product_name']}\n"
        f"💰 Цена (ориентировачная): {data['price']}\n\n"
        f"📝 Описание:\n{data['desc']}\n\n"
        f"🚚 Доставка: {data['delivery']}\n"
        f"📍 Адрес: {data['address']}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_text)
        except:
            pass

    # Отправляем новое сообщение с подтверждением
    await query.message.reply_text(
        f"✅ Заказ оформлен!\n\n"
        f"📋 Номер заказа: {order['order_number']}\n\n"
        f"Я скоро свяжусь с тобой для подтверждения 🤍\n\n"
        f"📍 Проверить статус заказа можно в разделе 'Мой заказ'\n"
        f"📱 Есть вопросы? Пиши @cblrokxx\n\n"
        f"💫 Спасибо, что выбрала мои работы!",
        reply_markup=main_menu()
    )

    # Удаляем сообщение с подтверждением
    try:
        await query.message.delete()
    except:
        pass

    del temp[user_id]
    return ConversationHandler.END


# ===== НАЗАД В ОФОРМЛЕНИИ ЗАКАЗА =====
async def order_back(update, context):
    """Обработчик кнопок назад при оформлении заказа"""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    action = query.data

    if action == "order_back_phone":
        # Возврат к вводу телефона
        await query.edit_message_text(
            "📱 Напиши номер телефона для связи:\n"
            "📌 Пример: +375 29 1234567",
            reply_markup=back_button()
        )
        return PHONE

    elif action == "order_back_product":
        # Возврат к выбору товара
        await query.edit_message_text(
            "🧸 Что заказываем?",
            reply_markup=product_menu()
        )
        return PRODUCT

    elif action == "order_back_delivery":
        # Возврат к выбору доставки
        await query.edit_message_text(
            "🚚 Выбери способ доставки",
            reply_markup=delivery_menu()
        )
        return DELIVERY

    elif action == "order_back_desc":
        # Возврат к описанию заказа
        user_id = str(update.effective_user.id)
        data = temp.get(user_id, {})

        await query.edit_message_text(
            f"📝 Опиши свой заказ\n\n"
            f"💰 Цена: {data.get('price', '')}\n\n"
            "Расскажи подробнее:\n"
            "• Какой цвет?\n"
            "• Какая внешность?\n"
            "• Особенности?\n"
            "• Ссылка на мудборд (если есть)\n\n"
            "💡 Чем подробнее, тем лучше получится ❤️",
            reply_markup=back_button()
        )
        return DESC

    return ConversationHandler.END


async def back(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎨 Главное меню",
        reply_markup=main_menu()
    )
    return ConversationHandler.END


# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(CLIENT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(my_order, pattern="^my_order$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order$")],
        states={
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
                CallbackQueryHandler(order_back, pattern="^order_back_phone$")
            ],
            PRODUCT: [
                CallbackQueryHandler(get_product, pattern="^product_"),
                CallbackQueryHandler(order_back, pattern="^order_back_phone$")
            ],
            DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc),
                CallbackQueryHandler(order_back, pattern="^order_back_product$")
            ],
            DELIVERY: [
                CallbackQueryHandler(get_delivery, pattern="^delivery_"),
                CallbackQueryHandler(order_back, pattern="^order_back_desc$")
            ],
            ADDR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_address),
                CallbackQueryHandler(order_back, pattern="^order_back_delivery$")
            ],
            CONFIRM: [
                CallbackQueryHandler(order_confirm, pattern="^confirm$"),
                CallbackQueryHandler(order_back, pattern="^order_back_delivery$"),
                CallbackQueryHandler(back, pattern="^back$")
            ],
        },
        fallbacks=[CallbackQueryHandler(back, pattern="^back$")],
    )
    app.add_handler(order_conv)

    review_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(review_start, pattern="^review_start$")],
        states={
            REVIEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, review_get_text)],
            REVIEW_RATING: [CallbackQueryHandler(review_get_rating, pattern="^rating_")],
        },
        fallbacks=[CallbackQueryHandler(back, pattern="^back$")],
    )
    app.add_handler(review_conv)

    print("🤖 Клиентский бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()