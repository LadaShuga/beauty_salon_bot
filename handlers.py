import logging
from aiogram import F, types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command

import database as db
import keyboards as kb
import datetime
"""Вся логика работы бота"""
logger = logging.getLogger(__name__)

# Состояния для FSM
class Booking(StatesGroup):
    master = State()
    service = State()
    date = State()
    time = State()
    confirm = State()


async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Команда /start от {message.from_user.id}")
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username
    )
    
    await message.answer(
        "👋 Добро пожаловать в салон красоты «Идеал»!\n\n"
        "✨ Мы создаем красоту и дарим вдохновение.\n"
        "Для записи мне нужен ваш номер телефона.",
        reply_markup=kb.phone_keyboard()
    )

async def contact_handler(message: Message):
    """Обработчик получения контакта"""
    if message.contact:
        phone = message.contact.phone_number
        db.add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            phone=phone
        )
        await message.answer(
            "✅ Спасибо! Теперь вы можете записаться.\n\n"
            "📅 Нажмите «Записаться», чтобы выбрать мастера и услугу.",
            reply_markup=kb.main_menu()
        )
    else:
        await message.answer("Пожалуйста, используйте кнопку.")


async def book_start(message: Message, state: FSMContext):
    """Начало процесса бронирования"""
    masters = db.get_masters()
    if not masters:
        await message.answer(
            "😔 Извините, сейчас нет доступных мастеров.\n"
            "Пожалуйста, попробуйте позже."
        )
        return
    
    await message.answer(
        "🎨 Выберите мастера:",
        reply_markup=kb.masters_keyboard(masters)
    )
    await state.set_state(Booking.master)


async def process_master(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора мастера"""
    await callback.answer()
    master_id = int(callback.data.split('_')[1])
    master = db.get_master(master_id)
    
    if not master:
        await callback.message.edit_text("Мастер не найден")
        return
    
    await state.update_data(master_id=master_id)
    
    _, name, specialty, photo_id, description, experience = master
    
    if photo_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=f"👤 <b>{name}</b>\n"
                    f"💼 {specialty}\n"
                    f"⏳ Опыт: {experience}\n\n"
                    f"📝 {description}\n\n"
                    f"Выберите услугу:",
            parse_mode="HTML",
            reply_markup=kb.services_keyboard(db.get_services_by_master(master_id))
        )
    else:
        await callback.message.edit_text(
            f"👤 <b>{name}</b> - {specialty}\n\n{description}\n\nВыберите услугу:",
            parse_mode="HTML",
            reply_markup=kb.services_keyboard(db.get_services_by_master(master_id))
        )
    
    await state.set_state(Booking.service)


async def process_service(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги"""
    await callback.answer()
    service_id = int(callback.data.split('_')[1])
    service = db.get_service(service_id)
    
    if not service:
        await callback.message.edit_text("Услуга не найдена")
        return
    
    service_id, name, duration, price, master_id, photo_id, description = service
    await state.update_data(service_id=service_id, duration=duration, master_id=master_id)
    
    available_dates = db.get_available_dates(master_id, duration, days_ahead=14)
    
    caption = f"💇 <b>{name}</b>\n"
    caption += f"⏱ Длительность: {duration} мин\n"
    caption += f"💰 Стоимость: {price}₽\n\n"
    caption += f"📋 {description}\n\n"
    
    if not available_dates:
        caption += "😔 К сожалению, у мастера нет свободных окон в ближайшие 2 недели.\n"
        caption += "Попробуйте выбрать другую услугу или мастера."
        reply_markup = None
    else:
        caption += f"📅 <b>Доступные даты ({len(available_dates)}):</b>"
        reply_markup = kb.date_keyboard(available_dates)
    
    if photo_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await callback.message.edit_text(
            caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    if available_dates:
        await state.set_state(Booking.date)


async def process_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    await callback.answer()
    
    if callback.data == "no_dates":
        await callback.message.edit_text(
            "😔 Нет доступных дат. Попробуйте выбрать другого мастера или услугу.",
            reply_markup=kb.main_menu()
        )
        await state.clear()
        return
    
    date_str = callback.data.split('_')[1]
    data = await state.get_data()
    master_id = data['master_id']
    service_duration = data['duration']
    
    free_slots = db.get_free_slots(master_id, date_str, service_duration)
    
    if not free_slots:
        available_dates = db.get_available_dates(master_id, service_duration, days_ahead=14)
        if available_dates:
            await callback.message.edit_text(
                "😔 Это время уже занято. Выберите другую дату:",
                reply_markup=kb.date_keyboard(available_dates)
            )
        else:
            await callback.message.edit_text(
                "😔 К сожалению, больше нет свободных дат.",
                reply_markup=kb.main_menu()
            )
            await state.clear()
        return
    
    await state.update_data(date=date_str)
    
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%d.%m.%Y')
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_of_week = days[date_obj.weekday()]
    
    await callback.message.edit_text(
        f"📅 <b>{day_of_week}, {formatted_date}</b>\n\n"
        f"Доступное время ({len(free_slots)} слотов):",
        parse_mode="HTML",
        reply_markup=kb.time_keyboard(free_slots)
    )
    
    await state.set_state(Booking.time)


async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    await callback.answer()
    time_str = callback.data.split('_')[1]
    await state.update_data(time=time_str)

    data = await state.get_data()
    master_id = data['master_id']
    service_id = data['service_id']
    date_str = data['date']
    duration = data['duration']

    free_slots = db.get_free_slots(master_id, date_str, duration)
    if time_str not in free_slots:
        await callback.message.edit_text(
            "❌ К сожалению, это время уже занято. Пожалуйста, выберите другое:",
            reply_markup=kb.time_keyboard(free_slots)
        )
        return

    master = db.get_master(master_id)
    service = db.get_service(service_id)
    
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_of_week = days[date_obj.weekday()]
    
    summary = (
        f"📝 <b>ПОДТВЕРЖДЕНИЕ ЗАПИСИ</b>\n\n"
        f"👤 <b>Мастер:</b> {master[1]}\n"
        f"💇 <b>Услуга:</b> {service[1]}\n"
        f"💰 <b>Стоимость:</b> {service[3]}₽\n"
        f"⏱ <b>Длительность:</b> {duration} мин\n\n"
        f"📅 <b>Дата:</b> {day_of_week}, {formatted_date}\n"
        f"⏰ <b>Время:</b> {time_str}\n\n"
        f"Все верно?"
    )
    
    if master[3]:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=master[3],
            caption=summary,
            parse_mode="HTML",
            reply_markup=kb.confirm_keyboard(service_id, master_id, date_str, time_str)
        )
    else:
        await callback.message.edit_text(
            summary,
            parse_mode="HTML",
            reply_markup=kb.confirm_keyboard(service_id, master_id, date_str, time_str)
        )
    
    await state.set_state(Booking.confirm)


async def process_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание записи"""
    await callback.answer()
    
    if callback.data == "cancel_booking":
        await callback.message.edit_text("❌ Запись отменена.")
        await state.clear()
        return

    parts = callback.data.split('_')
    if len(parts) < 5:
        await callback.message.edit_text("Ошибка в данных записи")
        await state.clear()
        return
        
    _, service_id, master_id, date_str, time_str = parts
    service_id = int(service_id)
    master_id = int(master_id)

    service = db.get_service(service_id)
    free_slots = db.get_free_slots(master_id, date_str, service[2])
    
    if time_str not in free_slots:
        await callback.message.edit_text(
            "❌ Извините, это время уже занято, пока вы думали.\n"
            "Попробуйте выбрать другое время."
        )
        await state.clear()
        return

    booking_id = db.create_booking(
        user_id=callback.from_user.id,
        master_id=master_id,
        service_id=service_id,
        booking_date=date_str,
        booking_time=time_str
    )

    if not booking_id:
        await callback.message.edit_text(
            "❌ Ошибка при создании записи. Возможно, это время уже занято."
        )
        await state.clear()
        return

    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    success_text = (
        f"✅ <b>ЗАПИСЬ ПОДТВЕРЖДЕНА!</b>\n\n"
        f"Номер записи: <b>{booking_id}</b>\n"
        f"📅 Дата: {formatted_date}\n"
        f"⏰ Время: {time_str}\n\n"
        f"Ждём вас в салоне! ✨"
    )
    
    await callback.message.edit_text(
        success_text,
        parse_mode="HTML"
    )
    
    await state.clear()


async def my_bookings(message: Message):
    """Показывает активные записи пользователя"""
    bookings = db.get_user_bookings(message.from_user.id)
    
    if not bookings:
        await message.answer(
            "📭 У вас пока нет активных записей.\n"
            "Нажмите «📅 Записаться», чтобы выбрать услугу.",
            reply_markup=kb.main_menu()
        )
        return

    text = "📋 <b>ВАШИ ЗАПИСИ</b>\n\n"
    
    for bid, mname, sname, bdate, btime, status in bookings:
        date_obj = datetime.datetime.strptime(bdate, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")
        
        text += f"🔹 <b>{formatted_date} в {btime}</b>\n"
        text += f"  👤 Мастер: {mname}\n"
        text += f"  💇 Услуга: {sname}\n"
        text += f"  🆔 Номер: {bid}\n\n"
    
    await message.answer(text, parse_mode="HTML")


async def cancel_booking_start(message: Message):
    """Начало процесса отмены записи"""
    bookings = db.get_user_bookings(message.from_user.id)
    
    if not bookings:
        await message.answer("У вас нет активных записей для отмены.")
        return

    await message.answer(
        "Выберите запись, которую хотите отменить:",
        reply_markup=kb.cancel_bookings_keyboard(bookings)
    )

async def process_cancel_booking(callback: CallbackQuery):
    """Обработка отмены конкретной записи"""
    await callback.answer()
    
    try:
        booking_id = int(callback.data.split('_')[1])
        db.cancel_booking(booking_id)
        await callback.message.edit_text("✅ Запись успешно отменена.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при отмене записи: {e}")


async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=kb.main_menu()
    )


async def unknown_command(message: Message):
    """Обработка неизвестных команд"""
    if message.text.startswith('/'):
        await message.answer(
            f"❌ Неизвестная команда: {message.text}\n"
            f"Доступные команды: /start, /admin"
        )

async def unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        "Я не понимаю эту команду. Пожалуйста, используйте кнопки меню.",
        reply_markup=kb.main_menu()
    )


def register_handlers(dp: Dispatcher):
    """Регистрирует все обработчики"""
    logger.info("Регистрация основных хендлеров...")
    
    # Команды
    dp.message.register(cmd_start, Command("start"))
    
    # Обработчики сообщений
    dp.message.register(contact_handler, F.content_type == "contact")
    dp.message.register(book_start, F.text == "📅 Записаться")
    dp.message.register(my_bookings, F.text == "📋 Мои записи")
    dp.message.register(cancel_booking_start, F.text == "❌ Отменить запись")
    dp.message.register(back_to_main, F.text == "🔙 Назад в меню")
    
    # Callback-обработчики (FSM)
    dp.callback_query.register(process_master, F.data.startswith("master_"), Booking.master)
    dp.callback_query.register(process_service, F.data.startswith("service_"), Booking.service)
    dp.callback_query.register(process_date, F.data.startswith("date_") | (F.data == "no_dates"), Booking.date)
    dp.callback_query.register(process_time, F.data.startswith("time_"), Booking.time)
    dp.callback_query.register(process_confirm, 
                               (F.data.startswith("confirm_") | (F.data == "cancel_booking")), 
                               Booking.confirm)
    
    # Обычные callback
    dp.callback_query.register(process_cancel_booking, F.data.startswith("cancel_"))
    
    # Обработчик для неизвестных команд
    dp.message.register(unknown_command, lambda msg: msg.text and msg.text.startswith('/'))
    
    # Обработчик для всего остального
    dp.message.register(unknown_message)
    
    logger.info("Основные хендлеры зарегистрированы")