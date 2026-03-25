"""
Утилиты для бота - общие функции форматирования и проверок
"""
import datetime
from typing import Optional, Tuple


# Дни недели на русском
DAYS_OF_WEEK = [
    "Понедельник", "Вторник", "Среда", "Четверг", 
    "Пятница", "Суббота", "Воскресенье"
]

# Сокращенные дни недели
DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Месяцы на русском
MONTHS = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек"
]


def format_date(date_str: str, format_type: str = "full") -> str:
    """
    Форматирует дату в читаемый вид
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        format_type: Тип форматирования ('full', 'short', 'button')
    
    Returns:
        Отформатированная строка даты
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return date_str
    
    if format_type == "full":
        return date_obj.strftime("%d.%m.%Y")
    elif format_type == "short":
        return date_obj.strftime("%d.%m")
    elif format_type == "button":
        day_str = date_obj.strftime("%d")
        month_str = MONTHS[date_obj.month - 1]
        weekday_str = DAYS_SHORT[date_obj.weekday()]
        return f"{day_str} {month_str}, {weekday_str}"
    else:
        return date_obj.strftime("%d.%m.%Y")


def get_day_of_week(date_str: str) -> str:
    """
    Возвращает день недели для даты
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
    
    Returns:
        Название дня недели
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return DAYS_OF_WEEK[date_obj.weekday()]
    except ValueError:
        return ""


def format_datetime(date_str: str, time_str: str) -> str:
    """
    Форматирует дату и время вместе
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        time_str: Время в формате HH:MM
    
    Returns:
        Отформатированная строка
    """
    day_of_week = get_day_of_week(date_str)
    formatted_date = format_date(date_str, "full")
    return f"{day_of_week}, {formatted_date} в {time_str}"


def parse_time_range(time_str: str) -> Optional[Tuple[str, str]]:
    """
    Парсит строку времени в формате "HH:MM HH:MM" или "off"
    
    Args:
        time_str: Строка времени
    
    Returns:
        Кортеж (start_time, end_time) или None для выходного
    """
    time_str = time_str.strip()
    
    if time_str.lower() == "off":
        return None
    
    try:
        parts = time_str.split()
        if len(parts) != 2:
            return None
        
        start, end = parts
        # Валидация формата времени
        datetime.datetime.strptime(start, "%H:%M")
        datetime.datetime.strptime(end, "%H:%M")
        
        return (start, end)
    except (ValueError, IndexError):
        return None


def validate_time_range(start: str, end: str) -> bool:
    """
    Проверяет, что время начала раньше времени окончания
    
    Args:
        start: Время начала в формате HH:MM
        end: Время окончания в формате HH:MM
    
    Returns:
        True если время корректно, False иначе
    """
    try:
        start_time = datetime.datetime.strptime(start, "%H:%M")
        end_time = datetime.datetime.strptime(end, "%H:%M")
        return start_time < end_time
    except ValueError:
        return False


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        Обрезанный текст
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_int(value: str, default: int = 0) -> int:
    """
    Безопасное преобразование строки в число
    
    Args:
        value: Строка для преобразования
        default: Значение по умолчанию
    
    Returns:
        Целое число
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
