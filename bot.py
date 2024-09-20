from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command, Text
from aiogram import Router
from config import token
import sqlite3
import logging
from datetime import datetime

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
logging.basicConfig(level=logging.INFO)

connect = sqlite3.connect("bank.db", check_same_thread=False)
cursor = connect.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lastname TEXT,
                phone_number VARCHAR(100)
);""")
cursor.execute("""CREATE TABLE IF NOT EXISTS user_info(
               user_id INTEGER PRIMARY KEY,
               username VARCHAR(150),
               first_name VARCHAR(150),
               last_name VARCHAR(150),
               balance INTEGER DEFAULT 0,
               data_regist DATETIME
);""")
connect.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS transfers (
            transfer_id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            recipient_id INTEGER,
            amount REAL,
            FOREIGN KEY(sender_id) REFERENCES users(user_id),
            FOREIGN KEY(recipient_id) REFERENCES users(user_id)
);""")
connect.commit()


async def transfer_funds(sender_id, recipient_id, amount):
    cursor.execute("UPDATE user_info SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
    cursor.execute("UPDATE user_info SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
    cursor.execute("INSERT INTO transfers (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                   (sender_id, recipient_id, amount))
    connect.commit()

def get_balance(user_id):
    cursor.execute(f"SELECT balance FROM user_info WHERE user_id= {user_id}")
    connect.commit()
    result = cursor.fetchone()
    return result[0] if result is not None else None


@router.message(Command('balance'))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance is not None:
        await message.answer(f"Ваш текущий баланс: {balance} сомов.")
    else:
        await message.answer("У вас пока нет счета. Для создания счета воспользуйтесь командой /start.")


class OrderPersonState(StatesGroup):
    lastname = State()
    username = State()
    phone_number = State()


builder = ReplyKeyboardBuilder()
builder.add(
    KeyboardButton(text="О нас"),
    KeyboardButton(text="Регистрация"),
    KeyboardButton(text="/balance"),
    KeyboardButton(text="/transfer"),
    KeyboardButton(text="/deposit")
)
key_buttons = builder.as_markup(resize_keyboard=True)


@router.message(Command('start'))
async def start(message: types.Message):
    cursor.execute(f"SELECT user_id FROM user_info WHERE user_id = {message.from_user.id};")
    a = cursor.fetchall()
    if not a:
        cursor.execute(f"""INSERT INTO user_info (user_id, username, first_name, last_name, data_regist) 
                        VALUES ('{message.from_user.id}',  
                                '{message.from_user.username}',
                                '{message.from_user.first_name}',
                                '{message.from_user.last_name}',
                                '{datetime.now()}'
        );""")
        connect.commit()
        