import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from config import ADMIN_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)

# ===== СОСТОЯНИЯ =====
COMPLETION_DATE = 1


# ===== ПРОВЕРКА АДМИНА =====
def is_admin(user_id):
    return user_id in ADMIN_IDS


# ===== КЛАВИАТУРЫ =====
def admin_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Все заказы", callback_data="all_orders")],
        [InlineKeyboardButton("🆕 Новые заказы", callback_data="new_orders")],
        [InlineKeyboardButton("⭐ Отзывы на модерации", callback_data="pending_reviews")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)


def order_actions(order_id):
    keyboard = [
        [InlineKeyboardButton("🔄 В работу", callback_data=f"status_{order_id}_processing")],
        [InlineKeyboardButton("✅ Готов", callback_data=f"status_{order_id}_ready")],
        [InlineKeyboardButton("🚚 Отправлен", callback_data=f"status_{order_id}_shipped")],
        [InlineKeyboardButton("📆 Указать дату готовности", callback_data=f"date_{order_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"status_{order_id}_cancelled")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def review_actions(review_id):
    keyboard = [
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_review_{review_id}")],
        [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_review_{review_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])


# ===== ОБРАБОТЧИКИ =====
async def start(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен.")
        return

    await update.message.reply_text(
        "👑 Панель администратора\n\n"
        "Управляй заказами и отзывами:",
        reply_markup=admin_menu()
    )


async def show_orders(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    if query.data == "new_orders":
        orders = db.get_new_orders()
        title = "🆕 Новые заказы"
    else:
        orders = db.get_all_orders()
        title = "📋 Все заказы"

    if not orders:
        await query.edit_message_text(
            "📭 Заказов нет.",
            reply_markup=admin_menu()
        )
        return

    status_names = {
        'new': '🆕 Новый',
        'processing': '🔄 В работе',
        'ready': '✅ Готов',
        'shipped': '🚚 Отправлен',
        'completed': '🏁 Выполнен',
        'cancelled': '❌ Отменен'
    }

    text = f"{title}\n\n"
    for order in orders[:10]:
        text += f"📋 {order['order_number']} | {order['client_name']}\n"
        text += f"📱 {order['client_phone']}\n"
        text += f"📊 {status_names.get(order['status'], order['status'])}\n"
        text += f"📅 {order['created_at'][:10]}\n\n"

    keyboard = []
    for order in orders[:10]:
        keyboard.append([
            InlineKeyboardButton(
                f"{order['order_number']} - {order['client_name']}",
                callback_data=f"view_{order['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def view_order(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    order_id = int(query.data.split('_')[1])
    order = db.client.table('orders').select('*').eq('id', order_id).execute().data[0]

    product_names = {
        'couple': '👫 парные брелочки',
        'toy': '🧸 игрушка',
        'heart': '❤️ брелок-сердечко'
    }

    status_names = {
        'new': '🆕 Новый',
        'processing': '🔄 В работе',
        'ready': '✅ Готов',
        'shipped': '🚚 Отправлен',
        'completed': '🏁 Выполнен',
        'cancelled': '❌ Отменен'
    }

    # Показываем username, если есть
    username_display = f"@{order.get('client_username')}" if order.get('client_username') else 'Не указан'

    text = (
        f"📋 Заказ {order['order_number']}\n\n"
        f"👤 Клиент: {order['client_name']}\n"
        f"📱 Телефон: {order['client_phone']}\n"
        f"🔹 Telegram: {username_display}\n\n"
        f"🧸 Тип: {product_names.get(order['product_type'], order['product_type'])}\n"
        f"📝 Описание:\n{order['description']}\n\n"
        f"🚚 Доставка: {order['delivery_method']}\n"
        f"📍 Адрес: {order['delivery_address']}\n\n"
        f"📊 Статус: {status_names.get(order['status'], order['status'])}\n"
        f"📅 Создан: {order['created_at'][:16]}"
    )

    if order.get('completion_date'):
        text += f"\n📆 Готовность: {order['completion_date']}"

    await query.edit_message_text(
        text,
        reply_markup=order_actions(order_id)
    )


async def change_status(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    parts = query.data.split('_')
    order_id = int(parts[1])
    status = parts[2]

    db.update_status(order_id, status)

    status_names = {
        'processing': '🔄 В работе',
        'ready': '✅ Готов',
        'shipped': '🚚 Отправлен',
        'cancelled': '❌ Отменен'
    }

    await query.edit_message_text(
        f"✅ Статус изменен на: {status_names.get(status, status)}",
        reply_markup=admin_menu()
    )


async def set_completion_date_start(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    order_id = int(query.data.split('_')[1])
    context.user_data['order_id'] = order_id

    await query.edit_message_text(
        "📆 Введи примерную дату готовности заказа\n\n"
        "📌 Формат: ДД.ММ.ГГГГ\n"
        "📌 Пример: 15.07.2024",
        reply_markup=back_button()
    )
    return COMPLETION_DATE


async def set_completion_date(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен.")
        return

    date = update.message.text
    order_id = context.user_data.get('order_id')

    if not order_id:
        await update.message.reply_text("❌ Ошибка. Попробуй снова.")
        return

    db.update_status(order_id, None, date)

    # Уведомляем клиента
    order = db.client.table('orders').select('*').eq('id', order_id).execute().data[0]
    if order:
        try:
            await context.bot.send_message(
                order['client_telegram_id'],
                f"📆 Обновление по заказу {order['order_number']}\n\n"
                f"Примерная дата готовности: {date}\n\n"
                f"Я скоро свяжусь с тобой 🤍"
            )
        except:
            pass

    await update.message.reply_text(
        f"✅ Дата готовности {date} установлена!\n\n"
        f"📱 Клиент получил уведомление.",
        reply_markup=admin_menu()
    )
    return ConversationHandler.END


async def pending_reviews(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    reviews = db.get_pending_reviews()

    if not reviews:
        await query.edit_message_text(
            "📭 Нет отзывов на модерации.",
            reply_markup=admin_menu()
        )
        return

    text = "⭐ Отзывы на модерации\n\n"
    for r in reviews[:5]:
        text += f"{'⭐' * r['rating']} {r['client_name']}:\n"
        text += f"{r['text'][:100]}{'...' if len(r['text']) > 100 else ''}\n"
        text += f"📅 {r['created_at'][:10]}\n\n"

    keyboard = []
    for r in reviews[:5]:
        keyboard.append([
            InlineKeyboardButton(
                f"📝 Отзыв от {r['client_name']}",
                callback_data=f"review_{r['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def view_review(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    review_id = int(query.data.split('_')[1])
    review = db.client.table('reviews').select('*').eq('id', review_id).execute().data[0]

    text = (
        f"⭐ Отзыв\n\n"
        f"👤 Клиент: {review['client_name']}\n"
        f"⭐ Оценка: {review['rating']}/5\n"
        f"📝 Текст:\n{review['text']}\n"
        f"📅 Создан: {review['created_at'][:16]}"
    )

    await query.edit_message_text(
        text,
        reply_markup=review_actions(review_id)
    )


async def approve_review(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    review_id = int(query.data.split('_')[2])
    db.approve_review(review_id)

    await query.edit_message_text(
        "✅ Отзыв одобрен и опубликован!",
        reply_markup=admin_menu()
    )


async def delete_review(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    review_id = int(query.data.split('_')[2])
    db.delete_review(review_id)

    await query.edit_message_text(
        "❌ Отзыв удален.",
        reply_markup=admin_menu()
    )


async def stats(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Доступ запрещен.")
        return

    orders = db.get_all_orders()
    reviews = db.get_approved_reviews()
    pending = db.get_pending_reviews()

    total = len(orders)
    new = len([o for o in orders if o['status'] == 'new'])
    processing = len([o for o in orders if o['status'] == 'processing'])
    completed = len([o for o in orders if o['status'] in ['ready', 'shipped', 'completed']])

    text = (
        "📊 Статистика\n\n"
        f"📦 Заказы:\n"
        f"  • Всего: {total}\n"
        f"  • Новые: {new}\n"
        f"  • В работе: {processing}\n"
        f"  • Выполнено: {completed}\n\n"
        f"⭐ Отзывы:\n"
        f"  • Опубликовано: {len(reviews)}\n"
        f"  • На модерации: {len(pending)}"
    )

    await query.edit_message_text(
        text,
        reply_markup=admin_menu()
    )


async def back(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👑 Панель администратора",
        reply_markup=admin_menu()
    )


# ===== ЗАПУСК =====
# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(ADMIN_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_orders, pattern="^all_orders$|^new_orders$"))
    app.add_handler(CallbackQueryHandler(view_order, pattern="^view_"))
    app.add_handler(CallbackQueryHandler(change_status, pattern="^status_"))
    app.add_handler(CallbackQueryHandler(set_completion_date_start, pattern="^date_"))
    app.add_handler(CallbackQueryHandler(pending_reviews, pattern="^pending_reviews$"))
    app.add_handler(CallbackQueryHandler(view_review, pattern="^review_"))
    app.add_handler(CallbackQueryHandler(approve_review, pattern="^approve_review_"))
    app.add_handler(CallbackQueryHandler(delete_review, pattern="^delete_review_"))
    app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    date_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_completion_date_start, pattern="^date_")],
        states={
            COMPLETION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_completion_date)],
        },
        fallbacks=[CallbackQueryHandler(back, pattern="^back$")],
    )
    app.add_handler(date_conv)

    print("👑 Админ-бот запущен!")

    # ОБХОД ОШИБКИ ДЛЯ RENDER
    try:
        app.run_polling()
    except RuntimeError as e:
        if "add_signal_handler" in str(e):
            import asyncio
            asyncio.run(app.run_polling())
        else:
            raise


if __name__ == "__main__":
    main()