
import sqlite3
import csv

from aiogram import F, types, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

import database as db
import keyboards as kb

from datetime import datetime, timedelta
"""Админ панель"""

import os
import logging

logger = logging.getLogger(__name__)

# Получаем строку с ID и преобразуем в список чисел
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]

def is_admin(user_id):
    return user_id in ADMIN_IDS  # Теперь сравниваем число с числами в списке

TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
    logger.info(f"Создана папка {TEMP_DIR}")

# Проверка на администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Состояния для админ-панели
class AdminStates(StatesGroup):
    # Для мастера
    add_master_name = State()
    add_master_specialty = State()
    add_master_description = State()
    add_master_experience = State()
    add_master_photo = State()
    
    # Для услуги
    add_service_name = State()
    add_service_duration = State()
    add_service_price = State()
    add_service_description = State()
    add_service_photo = State()
    add_service_master = State()
    
    # Для расписания
    edit_schedule_master = State()
    edit_schedule_day = State()
    edit_schedule_time = State()

# Главное меню админа

async def admin_panel(message: Message):
    """Главное меню админ-панели"""
    logger.info(f"Команда /admin от пользователя {message.from_user.id}")
    
    if not is_admin(message.from_user.id):
        logger.warning(f"Пользователь {message.from_user.id} не является админом")
        await message.answer("⛔ У вас нет прав администратора.")
        return
    
    await message.answer(
        "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=kb.admin_main_keyboard()
    )

# Управление мастерами

async def admin_masters(message: Message):
    """Управление мастерами"""
    if not is_admin(message.from_user.id):
        return
    
    masters = db.get_masters()
    
    if not masters:
        text = "📋 Список мастеров пуст.\n\nНажмите «➕ Добавить мастера» чтобы создать первого мастера."
    else:
        text = "📋 <b>СПИСОК МАСТЕРОВ</b>\n\n"
        for master in masters:
            master_id, name, specialty, photo_id, description, experience = master
            text += f"🆔 <b>{master_id}</b> | {name}\n"
            text += f"   💼 {specialty}\n"
            text += f"   ⏳ {experience}\n"
            if description:
                text += f"   📝 {description[:50]}...\n" if len(description) > 50 else f"   📝 {description}\n"
            text += "\n"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.admin_masters_keyboard()
    )


async def add_master_start(message: Message, state: FSMContext):
    """Начало добавления мастера"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МАСТЕРА</b> (шаг 1/5)\n\n"
        "Введите имя мастера:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_master_name)

async def add_master_name(message: Message, state: FSMContext):
    """Получение имени мастера"""
    await state.update_data(name=message.text)
    await message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МАСТЕРА</b> (шаг 2/5)\n\n"
        "Введите специализацию мастера (например: Парикмахер, Визажист):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_master_specialty)

async def add_master_specialty(message: Message, state: FSMContext):
    """Получение специализации"""
    await state.update_data(specialty=message.text)
    await message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МАСТЕРА</b> (шаг 3/5)\n\n"
        "Введите описание мастера:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_master_description)

async def add_master_description(message: Message, state: FSMContext):
    """Получение описания"""
    await state.update_data(description=message.text)
    await message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МАСТЕРА</b> (шаг 4/5)\n\n"
        "Введите опыт работы (например: 5 лет):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_master_experience)

async def add_master_experience(message: Message, state: FSMContext):
    """Получение опыта"""
    await state.update_data(experience=message.text)
    await message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МАСТЕРА</b> (шаг 5/5)\n\n"
        "Отправьте фото мастера (или отправьте /skip чтобы пропустить):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_master_photo)

async def add_master_photo(message: Message, state: FSMContext):
    """Получение фото мастера"""
    data = await state.get_data()
    
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    
    try:
        conn = sqlite3.connect('salon.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO masters (name, specialty, photo_id, description, experience)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data['specialty'], photo_id, data['description'], data['experience']))
        conn.commit()
        
        # Получаем ID нового мастера
        master_id = cur.lastrowid
        
        # Создаем базовое расписание для нового мастера
        days_of_week = range(7)
        for day in days_of_week:
            if day < 5:  # пн-пт
                cur.execute('''
                    INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                    VALUES (?, ?, ?, ?, ?)
                ''', (master_id, day, "10:00", "20:00", 1))
            else:  # сб-вс
                cur.execute('''
                    INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                    VALUES (?, ?, ?, ?, ?)
                ''', (master_id, day, "00:00", "00:00", 0))
        
        conn.commit()
        conn.close()
        
        await message.answer(
            "✅ Мастер успешно добавлен! Создано базовое расписание (пн-пт 10:00-20:00, сб-вс выходной).\n"
            "Вы можете отредактировать расписание в разделе «📅 Расписание».",
            reply_markup=kb.admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении мастера: {e}")
        await message.answer(f"❌ Ошибка при добавлении мастера: {e}")
    finally:
        await state.clear()

async def skip_master_photo(message: Message, state: FSMContext):
    """Пропуск добавления фото мастера"""
    if message.text == "/skip":
        data = await state.get_data()
        
        try:
            conn = sqlite3.connect('salon.db')
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO masters (name, specialty, photo_id, description, experience)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['name'], data['specialty'], None, data['description'], data['experience']))
            conn.commit()
            
            # Получаем ID нового мастера
            master_id = cur.lastrowid
            
            # Создаем базовое расписание для нового мастера
            days_of_week = range(7)
            for day in days_of_week:
                if day < 5:  # пн-пт
                    cur.execute('''
                        INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (master_id, day, "10:00", "20:00", 1))
                else:  # сб-вс
                    cur.execute('''
                        INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (master_id, day, "00:00", "00:00", 0))
            
            conn.commit()
            conn.close()
            
            await message.answer(
                "✅ Мастер успешно добавлен! Создано базовое расписание.",
                reply_markup=kb.admin_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении мастера: {e}")
            await message.answer(f"❌ Ошибка при добавлении мастера: {e}")
        finally:
            await state.clear()

# Просмотр конкретного мастера
async def view_master(callback: CallbackQuery):
    """Просмотр информации о мастере"""
    await callback.answer()
    master_id = int(callback.data.split('_')[2])
    master = db.get_master(master_id)
    
    if not master:
        await callback.message.edit_text("Мастер не найден")
        return
    
    _, name, specialty, photo_id, description, experience = master
    
    text = f"👤 <b>{name}</b>\n"
    text += f"💼 Специализация: {specialty}\n"
    text += f"⏳ Опыт: {experience}\n\n"
    text += f"📝 {description}\n\n"
    
    # Получить расписание 
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT day_of_week, start_time, end_time, is_working 
        FROM schedule 
        WHERE master_id=?
        ORDER BY day_of_week
    ''', (master_id,))
    schedule = cur.fetchall()
    conn.close()
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    text += "📅 <b>Расписание:</b>\n"
    if schedule:
        for day_data in schedule:
            day, start, end, is_working = day_data
            if is_working:
                text += f"   {days[day]}: {start} - {end}\n"
            else:
                text += f"   {days[day]}: Выходной\n"
    else:
        text += "   Расписание не настроено\n"
    
    if photo_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=text,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(text, parse_mode="HTML")

# Удаление мастера
async def delete_master_start(message: Message):
    """Начало удаления мастера"""
    if not is_admin(message.from_user.id):
        return
    
    masters = db.get_masters()
    if not masters:
        await message.answer("📋 Список мастеров пуст.")
        return
    
    await message.answer(
        "Выберите мастера для удаления:",
        reply_markup=kb.admin_masters_list_keyboard(masters, action="delete")
    )

async def delete_master_confirm(callback: CallbackQuery):
    """Подтверждение удаления мастера"""
    await callback.answer()
    master_id = int(callback.data.split('_')[2])
    
    try:
        conn = sqlite3.connect('salon.db')
        cur = conn.cursor()
        # Удаляем связанные услуги
        cur.execute("DELETE FROM services WHERE master_id=?", (master_id,))
        # Удаляем расписание
        cur.execute("DELETE FROM schedule WHERE master_id=?", (master_id,))
        # Удаляем записи к мастеру
        cur.execute("UPDATE bookings SET status='cancelled' WHERE master_id=?", (master_id,))
        # Удаляем мастера
        cur.execute("DELETE FROM masters WHERE id=?", (master_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text("✅ Мастер и все связанные данные удалены.")
    except Exception as e:
        logger.error(f"Ошибка при удалении мастера: {e}")
        await callback.message.edit_text(f"❌ Ошибка при удалении мастера: {e}")

# Управление услугами

async def admin_services(message: Message):
    """Управление услугами"""
    if not is_admin(message.from_user.id):
        return
    
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id, s.name, s.duration, s.price, m.name, s.description
        FROM services s
        JOIN masters m ON s.master_id = m.id
        ORDER BY m.name, s.name
    ''')
    services = cur.fetchall()
    conn.close()
    
    if not services:
        text = "📋 Список услуг пуст.\n\nНажмите «➕ Добавить услугу» чтобы создать первую услугу."
    else:
        text = "📋 <b>СПИСОК УСЛУГ</b>\n\n"
        current_master = ""
        for service in services:
            service_id, name, duration, price, master_name, description = service
            if master_name != current_master:
                current_master = master_name
                text += f"\n👤 <b>{master_name}</b>:\n"
            text += f"   🆔 {service_id} | {name} ({duration}мин) - {price}₽\n"
            if description:
                text += f"      📝 {description[:50]}...\n" if len(description) > 50 else f"      📝 {description}\n"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=kb.admin_services_keyboard()
    )

# Добавление услуги
async def add_service_start(message: Message, state: FSMContext):
    """Начало добавления услуги"""
    if not is_admin(message.from_user.id):
        return
    
    masters = db.get_masters()
    if not masters:
        await message.answer("❌ Сначала добавьте мастера!")
        return
    
    await message.answer(
        "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 1/6)\n\n"
        "Введите название услуги:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_service_name)

async def add_service_name(message: Message, state: FSMContext):
    """Получение названия услуги"""
    await state.update_data(name=message.text)
    await message.answer(
        "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 2/6)\n\n"
        "Введите длительность в минутах (например: 60):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_service_duration)

async def add_service_duration(message: Message, state: FSMContext):
    """Получение длительности"""
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer("❌ Длительность должна быть положительным числом")
            return
        await state.update_data(duration=duration)
        await message.answer(
            "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 3/6)\n\n"
            "Введите цену в рублях (например: 1500):",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_service_price)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")

async def add_service_price(message: Message, state: FSMContext):
    """Получение цены"""
    try:
        price = int(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть положительным числом")
            return
        await state.update_data(price=price)
        await message.answer(
            "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 4/6)\n\n"
            "Введите описание услуги:",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_service_description)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")

async def add_service_description(message: Message, state: FSMContext):
    """Получение описания"""
    await state.update_data(description=message.text)
    
    masters = db.get_masters()
    await message.answer(
        "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 5/6)\n\n"
        "Выберите мастера для этой услуги:",
        parse_mode="HTML",
        reply_markup=kb.admin_masters_list_keyboard(masters, action="service_master")
    )
    await state.set_state(AdminStates.add_service_master)

async def add_service_master(callback: CallbackQuery, state: FSMContext):
    """Выбор мастера для услуги"""
    await callback.answer()
    master_id = int(callback.data.split('_')[2])
    await state.update_data(master_id=master_id)
    
    await callback.message.edit_text(
        "💇 <b>ДОБАВЛЕНИЕ УСЛУГИ</b> (шаг 6/6)\n\n"
        "Отправьте фото примера работы (или /skip чтобы пропустить):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_service_photo)

async def add_service_photo(message: Message, state: FSMContext):
    """Получение фото услуги"""
    data = await state.get_data()
    
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    
    try:
        conn = sqlite3.connect('salon.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO services (name, duration, price, master_id, photo_id, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['duration'], data['price'], data['master_id'], photo_id, data['description']))
        conn.commit()
        conn.close()
        
        await message.answer(
            "✅ Услуга успешно добавлена!",
            reply_markup=kb.admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении услуги: {e}")
        await message.answer(f"❌ Ошибка при добавлении услуги: {e}")
    finally:
        await state.clear()

async def skip_service_photo(message: Message, state: FSMContext):
    """Пропуск добавления фото услуги"""
    if message.text == "/skip":
        data = await state.get_data()
        
        try:
            conn = sqlite3.connect('salon.db')
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO services (name, duration, price, master_id, photo_id, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['duration'], data['price'], data['master_id'], None, data['description']))
            conn.commit()
            conn.close()
            
            await message.answer(
                "✅ Услуга успешно добавлена!",
                reply_markup=kb.admin_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении услуги: {e}")
            await message.answer(f"❌ Ошибка при добавлении услуги: {e}")
        finally:
            await state.clear()

# Удаление услуги
async def delete_service_start(message: Message):
    """Начало удаления услуги"""
    if not is_admin(message.from_user.id):
        return
    
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id, s.name, m.name 
        FROM services s
        JOIN masters m ON s.master_id = m.id
        ORDER BY m.name, s.name
    ''')
    services = cur.fetchall()
    conn.close()
    
    if not services:
        await message.answer("📋 Список услуг пуст.")
        return
    
    await message.answer(
        "Выберите услугу для удаления:",
        reply_markup=kb.admin_services_list_keyboard(services)
    )

async def delete_service_confirm(callback: CallbackQuery):
    """Подтверждение удаления услуги"""
    await callback.answer()
    service_id = int(callback.data.split('_')[2])
    
    try:
        conn = sqlite3.connect('salon.db')
        cur = conn.cursor()
        # Проверяем, есть ли записи на эту услугу
        cur.execute("SELECT id FROM bookings WHERE service_id=? AND status='active'", (service_id,))
        if cur.fetchone():
            await callback.message.edit_text(
                "❌ Нельзя удалить услугу, на которую есть активные записи.\n"
                "Сначала отмените или завершите эти записи."
            )
            conn.close()
            return
        
        cur.execute("DELETE FROM services WHERE id=?", (service_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text("✅ Услуга успешно удалена.")
    except Exception as e:
        logger.error(f"Ошибка при удалении услуги: {e}")
        await callback.message.edit_text(f"❌ Ошибка при удалении услуги: {e}")

# Управление расписанием 

async def admin_schedule(message: Message):
    """Управление расписанием"""
    if not is_admin(message.from_user.id):
        return
    
    masters = db.get_masters()
    if not masters:
        await message.answer("❌ Сначала добавьте мастеров!")
        return
    
    # Создание клавиатуры динамически на основе списка мастеров
    builder = InlineKeyboardBuilder()
    for master in masters:
        master_id, name, specialty, _, _, _ = master
        builder.add(InlineKeyboardButton(
            text=f"👤 {name} ({specialty})",
            callback_data=f"schedule_view_{master_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    builder.adjust(1)
    
    await message.answer(
        "📅 <b>УПРАВЛЕНИЕ РАСПИСАНИЕМ</b>\n\n"
        "Выберите мастера для просмотра или редактирования расписания:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

async def view_schedule_master(callback: CallbackQuery, state: FSMContext):
    """Просмотр расписания мастера"""
    await callback.answer()
    master_id = int(callback.data.split('_')[2])
    
    # Получаем имя мастера
    master = db.get_master(master_id)
    if not master:
        await callback.message.edit_text("Мастер не найден")
        return
    
    # Получаем текущее расписание
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT day_of_week, start_time, end_time, is_working 
        FROM schedule 
        WHERE master_id=?
        ORDER BY day_of_week
    ''', (master_id,))
    schedule = cur.fetchall()
    conn.close()
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    text = f"👤 <b>{master[1]}</b>\n\n"
    text += "📅 <b>ТЕКУЩЕЕ РАСПИСАНИЕ</b>\n\n"
    
    if schedule:
        for day_data in schedule:
            day, start, end, is_working = day_data
            if is_working:
                text += f"• {days[day]}: {start} - {end}\n"
            else:
                text += f"• {days[day]}: Выходной\n"
    else:
        text += "Расписание не настроено. Нажмите «Редактировать» для создания расписания.\n"
    
    # Создаем клавиатуру с действиями
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✏️ Редактировать расписание",
        callback_data=f"schedule_edit_{master_id}"
    ))
    
    # Получаем список всех мастеров для кнопок "Сменить мастера"
    masters = db.get_masters()
    if len(masters) > 1:
        for m in masters:
            if m[0] != master_id:
                builder.add(InlineKeyboardButton(
                    text=f"👤 {m[1]}",
                    callback_data=f"schedule_view_{m[0]}"
                ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 Назад к списку мастеров",
        callback_data="back_to_schedule_masters"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

async def back_to_schedule_masters(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку мастеров в расписании"""
    await callback.answer()
    await state.clear()
    
    masters = db.get_masters()
    if masters:
        builder = InlineKeyboardBuilder()
        for master in masters:
            master_id, name, specialty, _, _, _ = master
            builder.add(InlineKeyboardButton(
                text=f"👤 {name} ({specialty})",
                callback_data=f"schedule_view_{master_id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        ))
        builder.adjust(1)
        
        await callback.message.edit_text(
            "📅 <b>УПРАВЛЕНИЕ РАСПИСАНИЕМ</b>\n\n"
            "Выберите мастера для просмотра или редактирования расписания:",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            "❌ Список мастеров пуст.",
            reply_markup=kb.admin_main_keyboard()
        )

async def edit_schedule_master(callback: CallbackQuery, state: FSMContext):
    """Выбор мастера для редактирования расписания"""
    await callback.answer()
    master_id = int(callback.data.split('_')[2])
    
    master = db.get_master(master_id)
    if not master:
        await callback.message.edit_text("Мастер не найден")
        return
    
    await state.update_data(master_id=master_id, master_name=master[1])
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    await callback.message.edit_text(
        f"👤 <b>{master[1]}</b>\n\n"
        "📅 <b>РЕДАКТИРОВАНИЕ РАСПИСАНИЯ</b>\n\n"
        "Выберите день для редактирования:",
        parse_mode="HTML",
        reply_markup=kb.admin_days_keyboard()
    )
    await state.set_state(AdminStates.edit_schedule_day)

async def edit_schedule_day(callback: CallbackQuery, state: FSMContext):
    """Выбор дня для редактирования"""
    await callback.answer()
    day = int(callback.data.split('_')[1])
    
    data = await state.get_data()
    master_name = data.get('master_name', 'Мастер')
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    await state.update_data(day=day, day_name=days[day])
    
    await callback.message.edit_text(
        f"👤 <b>{master_name}</b> | {days[day]}\n\n"
        "📅 <b>РЕДАКТИРОВАНИЕ ДНЯ</b>\n\n"
        "Отправьте время работы в формате:\n"
        "<code>10:00 20:00</code> - для рабочего дня\n"
        "<code>off</code> - для выходного\n\n"
        "Пример: 10:00 20:00",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.edit_schedule_time)

async def edit_schedule_time(message: Message, state: FSMContext):
    """Установка времени работы"""
    data = await state.get_data()
    master_id = data['master_id']
    master_name = data.get('master_name', 'Мастер')
    day = data['day']
    day_name = data.get('day_name', 'День')
    
    text = message.text.strip()
    
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id FROM schedule 
        WHERE master_id=? AND day_of_week=?
    ''', (master_id, day))
    
    exists = cur.fetchone()
    
    try:
        if text.lower() == 'off':
            if exists:
                cur.execute('''
                    UPDATE schedule 
                    SET start_time='00:00', end_time='00:00', is_working=0
                    WHERE master_id=? AND day_of_week=?
                ''', (master_id, day))
            else:
                cur.execute('''
                    INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                    VALUES (?, ?, ?, ?, ?)
                ''', (master_id, day, '00:00', '00:00', 0))
            
            conn.commit()
            await message.answer(
                f"✅ {day_name} установлен как выходной для {master_name}",
                reply_markup=kb.admin_main_keyboard()
            )
            
        else:
            try:
                start, end = text.split()
                datetime.strptime(start, "%H:%M")
                datetime.strptime(end, "%H:%M")
                
                start_time = datetime.strptime(start, "%H:%M")
                end_time = datetime.strptime(end, "%H:%M")
                if start_time >= end_time:
                    await message.answer("❌ Время начала должно быть раньше времени окончания")
                    conn.close()
                    return
                
                if exists:
                    cur.execute('''
                        UPDATE schedule 
                        SET start_time=?, end_time=?, is_working=1
                        WHERE master_id=? AND day_of_week=?
                    ''', (start, end, master_id, day))
                else:
                    cur.execute('''
                        INSERT INTO schedule (master_id, day_of_week, start_time, end_time, is_working)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (master_id, day, start, end, 1))
                
                conn.commit()
                await message.answer(
                    f"✅ Расписание для {master_name} на {day_name} обновлено: {start} - {end}",
                    reply_markup=kb.admin_main_keyboard()
                )
            except ValueError:
                await message.answer("❌ Неверный формат. Используйте: 10:00 20:00 или off")
                conn.close()
                return
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении расписания: {e}")
        await message.answer(f"❌ Ошибка при обновлении расписания: {e}")
    finally:
        conn.close()
        await state.clear()

# Экспорт данных 
async def admin_export(message: Message):
    """Экспорт данных в CSV"""
    if not is_admin(message.from_user.id):
        return
    
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(TEMP_DIR, filename)
    
    try:
        conn = sqlite3.connect('salon.db')
        cur = conn.cursor()
        
        cur.execute('''
            SELECT 
                b.id,
                u.username,
                u.phone,
                m.name as master,
                s.name as service,
                b.booking_date,
                b.booking_time,
                b.status,
                b.created_at
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.user_id
            LEFT JOIN masters m ON b.master_id = m.id
            LEFT JOIN services s ON b.service_id = s.id
            ORDER BY b.booking_date DESC, b.booking_time DESC
        ''')
        
        rows = cur.fetchall()
        conn.close()
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Клиент', 'Телефон', 'Мастер', 'Услуга', 'Дата', 'Время', 'Статус', 'Дата создания'])
            writer.writerows(rows)
        
        await message.answer_document(
            FSInputFile(filepath),
            caption=f"📊 Экспорт данных ({len(rows)} записей)"
        )
        
        os.remove(filepath)
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте: {e}")
        await message.answer(f"❌ Ошибка при экспорте: {e}")

# Возварт в главное меню

async def back_to_main_from_admin(message: Message, state: FSMContext):
    """Возврат из админ-панели в главное меню пользователя"""
    await state.clear()
    await message.answer(
        "🔙 Возврат в главное меню",
        reply_markup=kb.main_menu()
    )



async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено."
    )
    await callback.message.answer(
        "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=kb.admin_main_keyboard()
    )

# Регистрация Хендлеров
def register_admin_handlers(dp: Dispatcher):
    """Регистрирует обработчики админ-панели"""
    logger.info("Регистрация админ-хендлеров...")
    
    # Главное меню
    dp.message.register(admin_panel, Command("admin"))
    
    # Кнопки главного меню админки
    dp.message.register(admin_masters, F.text == "👥 Мастера")
    dp.message.register(admin_services, F.text == "💇 Услуги")
    dp.message.register(admin_schedule, F.text == "📅 Расписание")
    dp.message.register(admin_export, F.text == "📊 Экспорт")
    dp.message.register(back_to_main_from_admin, F.text == "🔙 Назад в меню")
    
    # Управление мастерами
    dp.message.register(add_master_start, F.text == "➕ Добавить мастера")
    dp.message.register(delete_master_start, F.text == "🗑 Удалить мастера")
    
    # Просмотр мастера
    dp.callback_query.register(view_master, F.data.startswith("view_master_"))
    
    # FSM для мастера
    dp.message.register(add_master_name, AdminStates.add_master_name)
    dp.message.register(add_master_specialty, AdminStates.add_master_specialty)
    dp.message.register(add_master_description, AdminStates.add_master_description)
    dp.message.register(add_master_experience, AdminStates.add_master_experience)
    dp.message.register(add_master_photo, AdminStates.add_master_photo, F.photo)
    dp.message.register(skip_master_photo, Command("skip"), AdminStates.add_master_photo)
    
    # Удаление мастера
    dp.callback_query.register(delete_master_confirm, F.data.startswith("delete_master_"))
    
    # Управление услугами
    dp.message.register(add_service_start, F.text == "➕ Добавить услугу")
    dp.message.register(delete_service_start, F.text == "🗑 Удалить услугу")
    
    # FSM для услуги
    dp.message.register(add_service_name, AdminStates.add_service_name)
    dp.message.register(add_service_duration, AdminStates.add_service_duration)
    dp.message.register(add_service_price, AdminStates.add_service_price)
    dp.message.register(add_service_description, AdminStates.add_service_description)
    dp.callback_query.register(add_service_master, F.data.startswith("service_master_"), AdminStates.add_service_master)
    dp.message.register(add_service_photo, AdminStates.add_service_photo, F.photo)
    dp.message.register(skip_service_photo, Command("skip"), AdminStates.add_service_photo)
    
    # Удаление услуги
    dp.callback_query.register(delete_service_confirm, F.data.startswith("delete_service_"))
    
    # Управление расписанием
    dp.callback_query.register(view_schedule_master, F.data.startswith("schedule_view_"))
    dp.callback_query.register(edit_schedule_master, F.data.startswith("schedule_edit_"))
    dp.callback_query.register(back_to_schedule_masters, F.data == "back_to_schedule_masters")
    dp.callback_query.register(edit_schedule_day, F.data.startswith("day_"), AdminStates.edit_schedule_day)
    dp.message.register(edit_schedule_time, AdminStates.edit_schedule_time)
    
    # Отмена
    dp.callback_query.register(cancel_callback, F.data == "cancel")
    
    logger.info("Админ-хендлеры зарегистрированы")
