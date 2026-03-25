from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import datetime
"""Файл для создания виртуальных кнопок и клавиатуры в боте"""

# Основаня клавиатура
def phone_keyboard():
    """Клавиатура для отправки номера телефона"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Отправить номер", request_contact=True))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def main_menu():
    """Главное меню пользователя"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📅 Записаться"))
    builder.add(KeyboardButton(text="📋 Мои записи"))
    builder.add(KeyboardButton(text="❌ Отменить запись"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def masters_keyboard(masters_list):
    """Клавиатура выбора мастера"""
    builder = InlineKeyboardBuilder()
    for mid, name, specialty, _, _, _ in masters_list:
        builder.add(InlineKeyboardButton(
            text=f"👤 {name} - {specialty}",
            callback_data=f"master_{mid}"
        ))
    builder.adjust(1)
    return builder.as_markup()

def services_keyboard(services_list):
    """Клавиатура выбора услуги"""
    builder = InlineKeyboardBuilder()
    for sid, name, duration, price, _, _ in services_list:
        builder.add(InlineKeyboardButton(
            text=f"💇 {name} ({duration}мин) - {price}₽",
            callback_data=f"service_{sid}"
        ))
    builder.adjust(1)
    return builder.as_markup()

def date_keyboard(available_dates):
    """Клавиатура выбора даты"""
    if not available_dates:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="😔 Нет свободных дат",
            callback_data="no_dates"
        ))
        return builder.as_markup()
    
    builder = InlineKeyboardBuilder()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    months = ["янв", "фев", "мар", "апр", "май", "июн", 
              "июл", "авг", "сен", "окт", "ноя", "дек"]
    
    for date_str in available_dates[:10]:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        day_str = date_obj.strftime("%d")
        month_str = months[date_obj.month - 1]
        weekday_str = days[date_obj.weekday()]
        
        button_text = f"{day_str} {month_str}, {weekday_str}"
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"date_{date_str}"
        ))
    
    builder.adjust(2)
    return builder.as_markup()

def time_keyboard(free_slots):
    """Клавиатура выбора времени"""
    builder = InlineKeyboardBuilder()
    for slot in free_slots:
        builder.add(InlineKeyboardButton(
            text=slot,
            callback_data=f"time_{slot}"
        ))
    builder.adjust(4)
    return builder.as_markup()

def confirm_keyboard(service_id, master_id, date_str, time_str):
    """Клавиатура подтверждения записи"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Подтвердить запись",
        callback_data=f"confirm_{service_id}_{master_id}_{date_str}_{time_str}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_booking"
    ))
    builder.adjust(1)
    return builder.as_markup()

def cancel_bookings_keyboard(bookings):
    """Клавиатура для отмены записей"""
    builder = InlineKeyboardBuilder()
    for bid, mname, sname, bdate, btime, status in bookings:
        date_obj = datetime.datetime.strptime(bdate, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m")
        
        btn_text = f"📅 {formatted_date} {btime} - {sname}"
        builder.add(InlineKeyboardButton(
            text=btn_text,
            callback_data=f"cancel_{bid}"
        ))
    builder.adjust(1)
    return builder.as_markup()

# Админ-панель

def admin_main_keyboard():
    """Главное меню админ-панели"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="👥 Мастера"))
    builder.add(KeyboardButton(text="💇 Услуги"))
    builder.add(KeyboardButton(text="📅 Расписание"))
    builder.add(KeyboardButton(text="📊 Экспорт"))
    builder.add(KeyboardButton(text="🔙 Назад в меню"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def admin_masters_keyboard():
    """Клавиатура управления мастерами"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="➕ Добавить мастера"))
    builder.add(KeyboardButton(text="🗑 Удалить мастера"))
    builder.add(KeyboardButton(text="🔙 Назад в меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def admin_services_keyboard():
    """Клавиатура управления услугами"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="➕ Добавить услугу"))
    builder.add(KeyboardButton(text="🗑 Удалить услугу"))
    builder.add(KeyboardButton(text="🔙 Назад в меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def admin_masters_list_keyboard(masters, action="select"):
    """
    Создает список мастеров для выбора
    action: select, delete, schedule, service_master, view
    """
    builder = InlineKeyboardBuilder()
    
    for master in masters:
        master_id, name, specialty, _, _, _ = master
        
        if action == "delete":
            callback_data = f"delete_master_{master_id}"
            text = f"🗑 {name} ({specialty})"
        elif action == "schedule":
            callback_data = f"schedule_view_{master_id}"
            text = f"📅 {name} ({specialty})"
        elif action == "service_master":
            callback_data = f"service_master_{master_id}"
            text = f"👤 {name} ({specialty})"
        elif action == "view":
            callback_data = f"view_master_{master_id}"
            text = f"👁 {name} ({specialty})"
        else:
            callback_data = f"select_master_{master_id}"
            text = f"{name} ({specialty})"
        
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    builder.adjust(1)
    return builder.as_markup()

def admin_services_list_keyboard(services):
    """Клавиатура списка услуг для удаления"""
    builder = InlineKeyboardBuilder()
    
    for service_id, name, master_name in services:
        builder.add(InlineKeyboardButton(
            text=f"🗑 {name} ({master_name})",
            callback_data=f"delete_service_{service_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    builder.adjust(1)
    return builder.as_markup()

def admin_days_keyboard():
    """Клавиатура выбора дня недели"""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    builder = InlineKeyboardBuilder()
    for i, day in enumerate(days):
        builder.add(InlineKeyboardButton(
            text=day,
            callback_data=f"day_{i}"
        ))
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    builder.adjust(1)
    return builder.as_markup()