import sqlite3
import datetime
import os


"""База данных для проекта"""


def migrate_db():
    """Обновляет структуру базы данных, добавляя недостающие колонки"""
    if not os.path.exists('salon.db'):
        print("📄 Файл БД не существует, миграция не требуется")
        return
    
    print("🔄 Проверка и обновление структуры базы данных...")
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    
    # Проверяем таблицу masters
    cur.execute("PRAGMA table_info(masters)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'photo_id' not in columns:
        try:
            cur.execute("ALTER TABLE masters ADD COLUMN photo_id TEXT")
            print("✅ Добавлена колонка photo_id в таблицу masters")
        except Exception as e:
            print(f"⚠️ Не удалось добавить photo_id: {e}")
    
    if 'description' not in columns:
        try:
            cur.execute("ALTER TABLE masters ADD COLUMN description TEXT")
            print("✅ Добавлена колонка description в таблицу masters")
        except Exception as e:
            print(f"⚠️ Не удалось добавить description: {e}")
    
    if 'experience' not in columns:
        try:
            cur.execute("ALTER TABLE masters ADD COLUMN experience TEXT")
            print("✅ Добавлена колонка experience в таблицу masters")
        except Exception as e:
            print(f"⚠️ Не удалось добавить experience: {e}")
    
    # Проверяем таблицу services
    cur.execute("PRAGMA table_info(services)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'photo_id' not in columns:
        try:
            cur.execute("ALTER TABLE services ADD COLUMN photo_id TEXT")
            print("✅ Добавлена колонка photo_id в таблицу services")
        except Exception as e:
            print(f"⚠️ Не удалось добавить photo_id в services: {e}")
    
    if 'description' not in columns:
        try:
            cur.execute("ALTER TABLE services ADD COLUMN description TEXT")
            print("✅ Добавлена колонка description в таблицу services")
        except Exception as e:
            print(f"⚠️ Не удалось добавить description в services: {e}")
    
    # Проверяем таблицу schedule
    cur.execute("PRAGMA table_info(schedule)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'is_working' not in columns:
        try:
            cur.execute("ALTER TABLE schedule ADD COLUMN is_working BOOLEAN DEFAULT 1")
            print("✅ Добавлена колонка is_working в таблицу schedule")
        except Exception as e:
            print(f"⚠️ Не удалось добавить is_working: {e}")
    
    conn.commit()
    conn.close()
    print("✨ Миграция базы данных завершена")

def init_db():
    """Создает таблицы при первом запуске"""
    current_dir = os.getcwd()
    db_path = os.path.join(current_dir, 'salon.db')
    print(f"📁 Работа с БД: {db_path}")
    
    db_exists = os.path.exists(db_path)
    if db_exists:
        print("📄 Файл БД существует, применяем миграцию...")
        migrate_db()
    else:
        print("🆕 Файл БД будет создан заново")
    
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()

    # Пользователи
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            phone TEXT,
            registered_at TEXT
        )
    ''')

    # Мастера
    cur.execute('''
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            specialty TEXT,
            photo_id TEXT,
            description TEXT,
            experience TEXT
        )
    ''')

    # Услуги
    cur.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            duration INTEGER,
            price INTEGER,
            master_id INTEGER,
            photo_id TEXT,
            description TEXT,
            FOREIGN KEY (master_id) REFERENCES masters (id)
        )
    ''')

    # Расписание мастера
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
            master_id INTEGER,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            is_working BOOLEAN DEFAULT 1,
            FOREIGN KEY (master_id) REFERENCES masters (id)
        )
    ''')

    # Записи
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            master_id INTEGER,
            service_id INTEGER,
            booking_date TEXT,
            booking_time TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (master_id) REFERENCES masters (id),
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Таблицы созданы/проверены")

# Функции для пользователей 

def add_user(user_id, username, phone=None):
    """Добавляет нового пользователя"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cur.execute('''
            INSERT OR REPLACE INTO users (user_id, username, phone, registered_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, phone, now))
        conn.commit()
    except sqlite3.IntegrityError:
        cur.execute('''
            UPDATE users SET username=?, phone=?, registered_at=?
            WHERE user_id=?
        ''', (username, phone, now, user_id))
        conn.commit()
    finally:
        conn.close()

def get_user(user_id):
    """Получает данные пользователя"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, phone FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    conn.close()
    return res

# Функции для мастеров 

def get_masters():
    """Получает список всех мастеров"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, specialty, photo_id, description, experience FROM masters ORDER BY name")
    res = cur.fetchall()
    conn.close()
    return res

def get_master(master_id):
    """Получает данные конкретного мастера"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, specialty, photo_id, description, experience FROM masters WHERE id=?", (master_id,))
    res = cur.fetchone()
    conn.close()
    return res

# Функции для услуг

def get_services_by_master(master_id):
    """Получает услуги конкретного мастера"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, duration, price, photo_id, description FROM services WHERE master_id=?", (master_id,))
    res = cur.fetchall()
    conn.close()
    return res

def get_service(service_id):
    """Получает данные конкретной услуги"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, duration, price, master_id, photo_id, description FROM services WHERE id=?", (service_id,))
    res = cur.fetchone()
    conn.close()
    return res

# Функции для расписания

def get_master_schedule(master_id, date):
    """Получает рабочие часы мастера на конкретную дату"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    day_of_week = date_obj.weekday()
    
    cur.execute('''
        SELECT start_time, end_time 
        FROM schedule 
        WHERE master_id = ? AND day_of_week = ? AND is_working = 1
    ''', (master_id, day_of_week))
    
    result = cur.fetchone()
    conn.close()
    return result

def get_booked_slots(master_id, date):
    """Получает все занятые слоты мастера на дату"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    
    cur.execute('''
        SELECT b.booking_time, s.duration
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE b.master_id = ? AND b.booking_date = ? AND b.status = 'active'
    ''', (master_id, date))
    
    booked = cur.fetchall()
    conn.close()
    return booked

def get_free_slots(master_id, date, service_duration):
    """
    Возвращает список свободных слотов для конкретной услуги
    """
    schedule = get_master_schedule(master_id, date)
    if not schedule:
        return []
    
    start_time, end_time = schedule
    start = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    
    booked = get_booked_slots(master_id, date)
    
    all_slots = []
    current = start
    while current + datetime.timedelta(minutes=service_duration) <= end:
        all_slots.append(current.strftime("%H:%M"))
        current += datetime.timedelta(minutes=30)
    
    free_slots = []
    for slot_time in all_slots:
        slot_start = datetime.datetime.strptime(f"{date} {slot_time}", "%Y-%m-%d %H:%M")
        slot_end = slot_start + datetime.timedelta(minutes=service_duration)
        
        is_free = True
        for booked_time, booked_duration in booked:
            booked_start = datetime.datetime.strptime(f"{date} {booked_time}", "%Y-%m-%d %H:%M")
            booked_end = booked_start + datetime.timedelta(minutes=booked_duration)
            
            if (slot_start < booked_end) and (slot_end > booked_start):
                is_free = False
                break
        
        if is_free:
            free_slots.append(slot_time)
    
    return free_slots

def get_available_dates(master_id, service_duration, days_ahead=14):
    """
    Возвращает список дат, в которые у мастера есть свободные слоты
    """
    available_dates = []
    today = datetime.date.today()
    
    for i in range(1, days_ahead + 1):
        check_date = today + datetime.timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        
        free_slots = get_free_slots(master_id, date_str, service_duration)
        
        if free_slots:
            available_dates.append(date_str)
    
    return available_dates

# Функции для записей

def create_booking(user_id, master_id, service_id, booking_date, booking_time):
    """Создает новую запись"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    cur.execute('''
        SELECT id FROM bookings
        WHERE master_id = ? AND booking_date = ? AND booking_time = ? AND status = 'active'
    ''', (master_id, booking_date, booking_time))
    
    if cur.fetchone():
        conn.close()
        return None
    
    cur.execute('''
        INSERT INTO bookings (user_id, master_id, service_id, booking_date, booking_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, master_id, service_id, booking_date, booking_time, now))
    
    conn.commit()
    booking_id = cur.lastrowid
    conn.close()
    return booking_id

def get_user_bookings(user_id):
    """Получает активные записи пользователя"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT b.id, m.name, s.name, b.booking_date, b.booking_time, b.status
        FROM bookings b
        JOIN masters m ON b.master_id = m.id
        JOIN services s ON b.service_id = s.id
        WHERE b.user_id = ? AND b.status = 'active'
        ORDER BY b.booking_date, b.booking_time
    ''', (user_id,))
    res = cur.fetchall()
    conn.close()
    return res

def cancel_booking(booking_id):
    """Отменяет запись"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

def is_master_busy(master_id, booking_date, booking_time, duration):
    """Проверяет, занят ли мастер в указанное время"""
    free_slots = get_free_slots(master_id, booking_date, duration)
    return booking_time not in free_slots

# Функции для очистки и диагностики

def clear_all_bookings():
    """Полностью очищает все записи"""
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings")
    cur.execute("DELETE FROM sqlite_sequence WHERE name='bookings'")
    conn.commit()
    conn.close()
    print("✅ Все записи удалены")

def show_database_status():
    """Показывает текущее состояние базы данных"""
    if not os.path.exists('salon.db'):
        print("❌ База данных не существует")
        return
    
    conn = sqlite3.connect('salon.db')
    cur = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 СОСТОЯНИЕ БАЗЫ ДАННЫХ".center(60))
    print("="*60)
    
    cur.execute("SELECT id, name, specialty FROM masters")
    masters = cur.fetchall()
    print(f"\n👥 Мастера ({len(masters)}):")
    for m in masters:
        print(f"  {m[0]}. {m[1]} - {m[2]}")
    
    cur.execute("SELECT id, name, duration, price, master_id FROM services")
    services = cur.fetchall()
    print(f"\n💇 Услуги ({len(services)}):")
    for s in services:
        print(f"  {s[0]}. {s[1]} ({s[2]}мин) - {s[3]}₽ (мастер {s[4]})")
    
    cur.execute("""
        SELECT b.id, u.username, m.name, s.name, b.booking_date, b.booking_time, b.status
        FROM bookings b
        LEFT JOIN users u ON b.user_id = u.user_id
        LEFT JOIN masters m ON b.master_id = m.id
        LEFT JOIN services s ON b.service_id = s.id
        ORDER BY b.booking_date, b.booking_time
    """)
    bookings = cur.fetchall()
    print(f"\n📅 Записи ({len(bookings)}):")
    for b in bookings:
        print(f"  {b[0]}. {b[4]} {b[5]} - {b[3]} у {b[2]} (клиент: {b[1]}, статус: {b[6]})")
    
    conn.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🔄 Инициализация базы данных...")
    init_db()
    show_database_status()
