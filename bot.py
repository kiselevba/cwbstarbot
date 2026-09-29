import asyncio
import sqlite3
import json
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo, Message

TOKEN = "8732302914:AAGf_rvj1Dnyo-QR7CmUQ5QSUi4KEpor1pM"
ADMIN_IDS = [514662828, 348370951]
BASE_WEBAPP_URL = "https://kiselevba.github.io/cwbstarbot/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СПРАВОЧНИК ДОСТИЖЕНИЙ (ТЗ) ---
TASKS = {
    "sales": {
        "name": "1. Продажи",
        "items": {
            "s1": {"name": "Выполнение личного плана продаж на протяжении трех месяцев подряд", "stars": 25},
            "s2": {"name": "Выполнение личного плана продаж на протяжении пяти месяцев подряд", "stars": 25},
            "s3": {"name": "Рекордная выручка за смену", "stars": 40},
            "s4": {"name": "Первое выполнение индивидуального плана продаж", "stars": 5},
            "s5": {"name": "Продал больше всех акций в период проведения", "stars": 10},
            "s6": {"name": "Выполнение плана продаж на 110 и более %", "stars": 15},
            "s7": {"name": "Выполнение плана", "stars": 3},
            "s8": {"name": "Продал больше всех единиц товара в период мотивации в своей категории", "stars": 7},
        }
    },
    "dev": {
        "name": "2. Личное развитие",
        "items": {
            "d1": {"name": "Прохождение стажировки и сдача экзамена для начала работы продавцом", "stars": 5},
            "d2": {"name": "Повышение до грейда “старший продавец”", "stars": 15},
            "d3": {"name": "Повышение до грейда “эксперт”", "stars": 25},
            "d4": {"name": "Успешное прохождение всех тренингов по продажам", "stars": 10},
        }
    },
    "qual": {
        "name": "3. Качество",
        "items": {
            "q1": {"name": "Ревизия с расхождением до 1000 руб. на протяжении 2 месяцев подряд", "stars": 7},
            "q2": {"name": "Успешная сдача стандартов по итогам двух проверок 32/32", "stars": 5},
            "q3": {"name": "Успешное прохождение проверки тайным покупателем на максимальный балл", "stars": 50},
        }
    },
    "init": {
        "name": "4. Инициатива",
        "items": {
            "i1": {"name": "Организация досуга команды", "stars": 5},
            "i2": {"name": "Организация и проведение обучения для сотрудников", "stars": 10},
            "i3": {"name": "Приведенный друг в компанию, который отработал 3 месяца", "stars": 15},
            "i4": {"name": "Наставничество новых сотрудников на протяжении месяца с конкретными результатами", "stars": 10},
            "i5": {"name": "Выход на подмену", "stars": 2},
            "i6": {"name": "Выход на экстренную подмену (уведомление за сутки и меньше до смены)", "stars": 5},
        }
    }
}

PRODUCTS = {
    "item_1": {"name": "Чаша Северный Космобол", "price": 5, "desc": "Отличная чаша, идеальна для крепких забивок."},
    "item_2": {"name": "Щипцы Муассель", "price": 7, "desc": "Удобные фирменные щипцы для работы с углем."},
    "item_3": {"name": "Такси до работы (эконом)", "price": 10, "desc": "Оплатим твою поездку на смену на такси."},
    "item_4": {"name": "Термостакан Муассель", "price": 10, "desc": "Стильный фирменный стакан."},
    "item_5": {"name": "Обнуление одного опоздания", "price": 15, "desc": "Прощаем одно опоздание до 15 минут."},
    "item_6": {"name": "Термокружка Муассель", "price": 15, "desc": "Фирменная кружка, долго держит тепло."},
    "item_7": {"name": "Обед на рабочем месте", "price": 15, "desc": "Доставка из KFC, BurgerKing или Вкусно и точка."},
    "item_8": {"name": "Энергетики HQD/Gorilla (12 шт)", "price": 15, "desc": "Месячный запас бодрости!"},
    "item_9": {"name": "Энергетики Monster (12 шт)", "price": 25, "desc": "Месячный запас крутого энергетика!"},
    "item_10": {"name": "Рандом бокс", "price": 25, "desc": "Сюрприз-бокс с секретным наполнением."},
    "item_11": {"name": "+15 тыс в личный план", "price": 30, "desc": "Помощь в выполнении личного плана продаж."},
    "item_12": {"name": "Сертификат Золотое Яблоко", "price": 40, "desc": "Подарочный сертификат на 3000 рублей."},
    "item_13": {"name": "Рюкзак Муассель", "price": 45, "desc": "Вместительный фирменный рюкзак."},
    "item_14": {"name": "Кофта Муассель (размер S)", "price": 55, "desc": "Уютная фирменная кофта."},
    "item_15": {"name": "Глэмпинг «Лесотерапия»", "price": 65, "desc": "Суточный отдых на двоих на природе."},
    "item_16": {"name": "Премия 7 000 руб.", "price": 90, "desc": "Приятная денежная прибавка."},
    "item_17": {"name": "Невыход на подмены (2 мес)", "price": 100, "desc": "Официальное освобождение от подмен."},
    "item_18": {"name": "Кальян Alpha", "price": 180, "desc": "Модели на выбор: X, Enzo, ОСД, Gold, Биты."},
    "item_19": {"name": "Премия 15 000 руб.", "price": 200, "desc": "Мощный денежный бонус!"},
    "item_20": {"name": "Чаша Хука", "price": 350, "desc": "Эксклюзивный ценный приз!"}
}

def get_now_str():
    return (datetime.utcnow() + timedelta(hours=5)).strftime("%d.%m.%Y %H:%M")

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (tg_id INTEGER PRIMARY KEY, full_name TEXT, balance INTEGER DEFAULT 0, 
                       role TEXT DEFAULT 'user', survey_completed INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id INTEGER, amount INTEGER, 
                       type TEXT, description TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS survey_answers
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id INTEGER, q1 TEXT, q2 TEXT, q3 TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id INTEGER, item_name TEXT, price INTEGER, status TEXT DEFAULT 'pending', date TEXT)''')
    conn.commit()
    conn.close()

class Registration(StatesGroup): waiting_for_name = State()
class AdminAddStars(StatesGroup): waiting_for_comment = State()

def get_main_keyboard(tg_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user = cursor.execute("SELECT balance, survey_completed FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    history = cursor.execute("SELECT amount, type, description, date FROM transactions WHERE tg_id = ? ORDER BY id DESC LIMIT 10", (tg_id,)).fetchall()
    
    balance = user[0] if user else 0
    survey_done = user[1] if user else 0
    is_admin = 1 if tg_id in ADMIN_IDS else 0
    
    users_list = []
    orders_list = []
    
    if is_admin:
        all_users = cursor.execute("SELECT tg_id, full_name, balance, survey_completed FROM users").fetchall()
        for u in all_users:
            users_list.append({"id": u[0], "name": u[1], "balance": u[2], "survey": u[3]})
            
        pending_orders = cursor.execute("SELECT orders.id, users.full_name, orders.item_name, orders.price, orders.date FROM orders JOIN users ON orders.tg_id = users.tg_id WHERE orders.status = 'pending'").fetchall()
        for o in pending_orders:
            orders_list.append({"id": o[0], "emp": o[1], "item": o[2], "price": o[3], "date": o[4]})
            
    conn.close()
    
    history_str = ",".join([f"{h[0]}|{h[1]}|{h[2]}|{h[3]}" for h in history]) if history else "empty"
    import urllib.parse
    encoded_history = urllib.parse.quote(history_str)
    
    encoded_users = urllib.parse.quote(json.dumps(users_list, ensure_ascii=False))
    encoded_orders = urllib.parse.quote(json.dumps(orders_list, ensure_ascii=False))

    webapp_url = f"{BASE_WEBAPP_URL}?bal={balance}&survey={survey_done}&admin={is_admin}&users={encoded_users}&orders={encoded_orders}&history={encoded_history}&t={int(time.time())}"

    kb = [
        [KeyboardButton(text="🌟 Открыть Mini App", web_app=WebAppInfo(url=webapp_url))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌟 Начислить звезды"), KeyboardButton(text="👥 Список сотрудников")],
        [KeyboardButton(text="🔙 Выйти из админки")]
    ], resize_keyboard=True)

@dp.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('database.db')
    user = conn.cursor().execute("SELECT full_name FROM users WHERE tg_id = ?", (message.from_user.id,)).fetchone()
    conn.close()
    if user:
        await message.answer(f"Главное меню открыто, {user[0]}:", reply_markup=get_main_keyboard(message.from_user.id))
    else:
        await message.answer("Привет! Пожалуйста, напиши свои Имя и Фамилию для регистрации.")
        await state.set_state(Registration.waiting_for_name)

@dp.message(Registration.waiting_for_name)
async def register_name(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (tg_id, full_name) VALUES (?, ?)", (message.from_user.id, message.text))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer(f"Отлично, {message.text}! Регистрация завершена.", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("👑 Панель управления", reply_markup=get_admin_keyboard())

@dp.message(F.text == "🔙 Выйти из админки")
async def exit_admin(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Открыто меню.", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "👥 Список сотрудников")
async def admin_list_users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('database.db')
    users = conn.cursor().execute("SELECT full_name, balance, survey_completed FROM users").fetchall()
    conn.close()
    
    if not users:
        return await message.answer("В базе пока нет зарегистрированных сотрудников.")
    
    text = "👥 **Список сотрудников CWB:**\n\n"
    for idx, (name, bal, survey) in enumerate(users, 1):
        survey_status = "✅ Прошел" if survey == 1 else "❌ Не прошел"
        text += f"{idx}. **{name}**\n   └ Баланс: {bal} ⭐️️ | Опрос: {survey_status}\n\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🌟 Начислить звезды")
async def admin_start_add_stars(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('database.db')
    users = conn.cursor().execute("SELECT tg_id, full_name FROM users").fetchall()
    conn.close()
    if not users: return await message.answer("Нет сотрудников.")
    kb = [[InlineKeyboardButton(text=f_name, callback_data=f"give_{u_id}")] for u_id, f_name in users]
    await message.answer("👤 Выбери сотрудника:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message(F.web_app_data)
async def process_web_app_data(message: Message):
    data_str = message.web_app_data.data
    
    # Запрос детальной истории сотрудника из Mini App (формат: view_user|tg_id)
    if data_str.startswith("view_user|"):
        if message.from_user.id not in ADMIN_IDS: return
        _, target_id_str = data_str.split("|")
        target_id = int(target_id_str)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user = cursor.execute("SELECT full_name, balance, survey_completed FROM users WHERE tg_id = ?", (target_id,)).fetchone()
        txs = cursor.execute("SELECT amount, type, description, date FROM transactions WHERE tg_id = ? ORDER BY id DESC LIMIT 15", (target_id,)).fetchall()
        conn.close()
        
        if user:
            name, bal, survey = user
            survey_text = "✅ Пройден" if survey == 1 else "❌ Не пройден"
            text = f"👤 **Сотрудник:** {name}\n⭐️ **Баланс:** {bal} звезд\n📝 **Опрос:** {survey_text}\n\n📜 **Последние операции:**\n"
            if txs:
                for amount, t_type, desc, date in txs:
                    text += f"{'🟢' if t_type=='income' else '🔴'} `{date}` | {'+' if t_type=='income' else '-'}{amount} ⭐️\n└ _{desc}_\n\n"
            else:
                text += "Операций пока нет."
            await message.answer(text, parse_mode="Markdown")
        return

    if data_str.startswith("order_app|") or data_str.startswith("order_rej|"):
        if message.from_user.id not in ADMIN_IDS: return
        action, order_id_str = data_str.split("|")
        order_id = int(order_id_str)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        order = cursor.execute("SELECT tg_id, item_name, price FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order:
            t_id, item_name, price = order
            if action == "order_app":
                cursor.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
                conn.commit()
                await message.answer(f"✅ Заказ на «{item_name}» одобрен.")
                try: await bot.send_message(t_id, f"🎉 Ваша заявка на **{item_name}** одобрена руководителем!")
                except: pass
            else:
                cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
                curr_bal = cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (t_id,)).fetchone()[0]
                new_bal = curr_bal + price
                cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (new_bal, t_id))
                cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", 
                               (t_id, price, 'income', f"Возврат за отказ: {item_name}", get_now_str()))
                conn.commit()
                await message.answer(f"❌ Заказ на «{item_name}» отклонен, звезды возвращены.")
                try: await bot.send_message(t_id, f"😔 Заявка на **{item_name}** отклонена. {price} ⭐️ возвращены на баланс.")
                except: pass
        conn.close()
        await message.answer("Меню обновлено:", reply_markup=get_main_keyboard(message.from_user.id))
        return

    if data_str.startswith("give_task|"):
        if message.from_user.id not in ADMIN_IDS: return
        _, target_id_str, cat_id, task_id = data_str.split("|", 3)
        target_id = int(target_id_str)
        task = TASKS[cat_id]["items"][task_id]
        amount = task["stars"]
        reason = task["name"]

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        curr_bal, full_name = cursor.execute("SELECT balance, full_name FROM users WHERE tg_id = ?", (target_id,)).fetchone()
        new_balance = curr_bal + amount
        cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (new_balance, target_id))
        cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", 
                       (target_id, amount, 'income', reason, get_now_str()))
        conn.commit()
        conn.close()

        await message.answer(f"✅ Начислено {amount} ⭐️ сотруднику **{full_name}** за «{reason}»!", parse_mode="Markdown")
        try:
            await bot.send_message(target_id, f"🎉 Вам начислено **{amount} ⭐️**!\nЗа достижение: {reason}\n\nБаланс: {new_balance} ⭐️", parse_mode="Markdown")
        except: pass
        await message.answer("Меню обновлено:", reply_markup=get_main_keyboard(message.from_user.id))
        return

    if data_str == "get_balance":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user_data = cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (message.from_user.id,)).fetchone()
        history = cursor.execute("SELECT amount, type, description, date FROM transactions WHERE tg_id = ? ORDER BY id DESC LIMIT 5", (message.from_user.id,)).fetchall()
        conn.close()
        
        balance = user_data[0] if user_data else 0
        text = f"⭐️ **Твой актуальный баланс:** {balance} звезд\n\n📜 **Последние операции:**\n"
        for amount, t_type, desc, date in history:
            text += f"{'🟢' if t_type=='income' else '🔴'} `{date}` | {'+' if t_type=='income' else '-'}{amount} ⭐️\n└ _{desc}_\n\n"
        await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))
        return

    if data_str.startswith("survey|"):
        _, q1, q2, q3 = data_str.split("|", 3)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        completed = cursor.execute("SELECT survey_completed FROM users WHERE tg_id = ?", (message.from_user.id,)).fetchone()[0]
        if completed == 1:
            conn.close()
            return await message.answer("✅ Ты уже проходил опрос ранее.")

        cursor.execute("INSERT INTO survey_answers (tg_id, q1, q2, q3, date) VALUES (?, ?, ?, ?, ?)", 
                       (message.from_user.id, q1, q2, q3, get_now_str()))
        cursor.execute("UPDATE users SET survey_completed = 1 WHERE tg_id = ?", (message.from_user.id,))
        curr_bal = cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (message.from_user.id,)).fetchone()[0]
        cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (curr_bal + 1, message.from_user.id))
        cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", 
                       (message.from_user.id, 1, 'income', 'Бонус за прохождение опроса', get_now_str()))
        conn.commit()
        conn.close()
        await message.answer("✅ Спасибо за ответы!\n\n🎉 За прохождение опроса начислена **1 ⭐️**!", parse_mode="Markdown")
        await message.answer("Меню обновлено:", reply_markup=get_main_keyboard(message.from_user.id))
        return

    item_id = data_str
    item = PRODUCTS.get(item_id)
    if not item: return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    balance, full_name = cursor.execute("SELECT balance, full_name FROM users WHERE tg_id = ?", (message.from_user.id,)).fetchone()
    
    if balance >= item['price']:
        new_balance = balance - item['price']
        cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (new_balance, message.from_user.id))
        cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", 
                       (message.from_user.id, item['price'], 'expense', f"Заявка: {item['name']}", get_now_str()))
        cursor.execute("INSERT INTO orders (tg_id, item_name, price, date) VALUES (?, ?, ?, ?)", 
                       (message.from_user.id, item['name'], item['price'], get_now_str()))
        conn.commit()
        
        await message.answer(f"⏳ Заявка на **{item['name']}** отправлена руководителю!\nСписано: {item['price']} ⭐️\nОстаток: {new_balance} ⭐️", parse_mode="Markdown")
        
        for a_id in ADMIN_IDS:
            try: await bot.send_message(a_id, f"🔔 **ЗАКАЗ ИЗ WEB-МАГАЗИНА!**\n\nСотрудник: {full_name}\nТовар: {item['name']}\nЦена: {item['price']} ⭐️", parse_mode="Markdown")
            except: pass
    else:
        await message.answer(f"❌ Недостаточно звезд для покупки **{item['name']}** (нужно {item['price']} ⭐️, а у тебя {balance} ⭐️).")
    conn.close()
    await message.answer("Меню обновлено:", reply_markup=get_main_keyboard(message.from_user.id))

async def main():
    init_db()
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
