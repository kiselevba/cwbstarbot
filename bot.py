import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo

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
    conn.commit()
    conn.close()

class Registration(StatesGroup): waiting_for_name = State()
class AdminAddStars(StatesGroup): waiting_for_comment = State()

def get_main_keyboard(tg_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user = cursor.execute("SELECT balance, survey_completed FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    history = cursor.execute("SELECT amount, type, description, date FROM transactions WHERE tg_id = ? ORDER BY id DESC LIMIT 10", (tg_id,)).fetchall()
    conn.close()
    
    balance = user[0] if user else 0
    survey_done = user[1] if user else 0
    
    history_str = ",".join([f"{h[0]}|{h[1]}|{h[2]}|{h[3]}" for h in history]) if history else "empty"
    import urllib.parse
    encoded_history = urllib.parse.quote(history_str)

    webapp_url = f"{BASE_WEBAPP_URL}?bal={balance}&survey={survey_done}&history={encoded_history}"

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
        survey_status = "✅ Прошел"
        text += f"{idx}. **{name}**\n   └ Баланс: {bal} ⭐️ | Опрос: {survey_status}\n\n"
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

@dp.callback_query(F.data.startswith("give_"))
async def admin_choose_user(callback: CallbackQuery, state: FSMContext):
    target_user_id = callback.data.replace("give_", "")
    await state.update_data(target_user_id=target_user_id)
    kb = [[InlineKeyboardButton(text=cat_data["name"], callback_data=f"acat|{cat_id}")] for cat_id, cat_data in TASKS.items()]
    await callback.message.edit_text("🗂 Выбери категорию достижений:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("acat|"))
async def admin_choose_category(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split("|")[1]
    kb = [[InlineKeyboardButton(text=f"{t_data['name']} (+{t_data['stars']} ⭐️)", callback_data=f"atsk|{cat_id}|{t_id}")] for t_id, t_data in TASKS[cat_id]["items"].items()]
    kb.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="back_to_cat")])
    await callback.message.edit_text(f"Категория: **{TASKS[cat_id]['name']}**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_cat")
async def admin_back_to_cat(callback: CallbackQuery, state: FSMContext):
    kb = [[InlineKeyboardButton(text=c_data["name"], callback_data=f"acat|{c_id}")] for c_id, c_data in TASKS.items()]
    await callback.message.edit_text("🗂 Выбери категорию достижений:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("atsk|"))
async def admin_choose_task(callback: CallbackQuery, state: FSMContext):
    _, cat_id, task_id = callback.data.split("|")
    task = TASKS[cat_id]["items"][task_id]
    await state.update_data(cat_id=cat_id, task_id=task_id)
    await callback.message.edit_text(f"🎯 Выбрано: **{task['name']}** (+{task['stars']} ⭐️)\n\nНапиши комментарий (или отправь `-`):", parse_mode="Markdown")
    await state.set_state(AdminAddStars.waiting_for_comment)

@dp.message(AdminAddStars.waiting_for_comment)
async def admin_enter_comment(message: types.Message, state: FSMContext):
    comment = message.text
    data = await state.get_data()
    target_user_id = int(data['target_user_id'])
    task = TASKS[data['cat_id']]["items"][data['task_id']]
    amount = task["stars"]
    
    reason = task['name']
    if comment != "-": reason += f" ({comment})"
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    curr_bal, full_name = cursor.execute("SELECT balance, full_name FROM users WHERE tg_id = ?", (target_user_id,)).fetchone()
    new_balance = curr_bal + amount
    cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (new_balance, target_user_id))
    cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", 
                   (target_user_id, amount, 'income', reason, get_now_str()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ Сотруднику **{full_name}** начислено {amount} ⭐️.", parse_mode="Markdown")
    try: 
        msg_text = f"🎉 **ПОЗДРАВЛЯЕМ!** 🎉\n\nТебе начислено **{amount} ⭐️**!\nЗа что: {task['name']}"
        if comment != "-": msg_text += f"\nКомментарий: _{comment}_"
        msg_text += f"\n\nБаланс: {new_balance} ⭐️"
        await bot.send_message(target_user_id, msg_text, parse_mode="Markdown")
    except: pass

@dp.message(F.web_app_data)
async def process_web_app_data(message: types.Message):
    data_str = message.web_app_data.data
    
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
        return await message.answer(text, parse_mode="Markdown")

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
        return await message.answer("✅ Спасибо за ответы!\n\n🎉 За прохождение опроса начислена **1 ⭐️**!", parse_mode="Markdown")

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
        conn.commit()
        
        await message.answer(f"⏳ Заявка на **{item['name']}** отправлена руководителю!\nСписано: {item['price']} ⭐️\nОстаток: {new_balance} ⭐️", parse_mode="Markdown")
        
        adm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_app|{message.from_user.id}|{item_id}|{item['price']}")], 
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_rej|{message.from_user.id}|{item_id}|{item['price']}")]
        ])
        username_info = f" (@{message.from_user.username})" if message.from_user.username else ""
        for a_id in ADMIN_IDS:
            try: await bot.send_message(a_id, f"🔔 **ЗАКАЗ ИЗ WEB-МАГАЗИНА!**\n\nСотрудник: {full_name}{username_info}\nТовар: {item['name']}\nЦена: {item['price']} ⭐️", reply_markup=adm_kb, parse_mode="Markdown")
            except: pass
    else:
        await message.answer(f"❌ Недостаточно звезд для покупки **{item['name']}** (нужно {item['price']} ⭐️, а у тебя {balance} ⭐️).")
    conn.close()

@dp.callback_query(F.data.startswith("adm_app|"))
async def admin_approve(callback: CallbackQuery):
    _, user_id, item_id, _ = callback.data.split("|")
    await callback.message.edit_text(f"✅ Одобрено: **{PRODUCTS[item_id]['name']}**.", parse_mode="Markdown")
    try: await bot.send_message(int(user_id), f"🎉 Твоя заявка на **{PRODUCTS[item_id]['name']}** одобрена!")
    except: pass

@dp.callback_query(F.data.startswith("adm_rej|"))
async def admin_reject(callback: CallbackQuery):
    _, user_id, item_id, price = callback.data.split("|")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    bal = cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (int(user_id),)).fetchone()[0]
    cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (bal + int(price), int(user_id)))
    cursor.execute("INSERT INTO transactions (tg_id, amount, type, description, date) VALUES (?, ?, ?, ?, ?)", (int(user_id), int(price), 'income', f"Возврат: {PRODUCTS[item_id]['name']}", get_now_str()))
    conn.commit()
    conn.close()
    await callback.message.edit_text(f"❌ Отклонено: **{PRODUCTS[item_id]['name']}**.", parse_mode="Markdown")
    try: await bot.send_message(int(user_id), f"😔 Заявка на **{PRODUCTS[item_id]['name']}** отклонена. {price} ⭐️ возвращены.")
    except: pass

async def main():
    init_db()
    print("🚀 Бот запущен (Админка расширена)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())