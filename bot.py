import os
import logging
import sqlite3
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

BOT_TOKEN = "8344884558:AAGnQyxzYUnKJYgaT-gQQ2Twv6xzr8wLGnA"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLy09Ie2igKzBhN6kPnYYHTO4QN2Si2AM3jRvFAgbjced91CepsdJdkGMEQv4uuQF9Yg/exec"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Web server for Render
async def handle_render(request):
    return web.Response(text="DUEVASUE Bot Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER PRIMARY KEY,
            full_name TEXT,
            sex TEXT,
            phone TEXT,
            department TEXT,
            year TEXT,
            campus TEXT
        )
    ''')
    conn.commit()
    conn.close()

class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    sex = State()
    year = State()
    campus = State()

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 የህብረቱ አባል መሆን (Register)", callback_data="menu_register")]
    ])

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("እንኳን ወደ ዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት ቦት በደህና መጡ!", reply_markup=get_main_menu())

@dp.callback_query(lambda c: c.data == "menu_register")
async def start_registration(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("📝 እባክዎ **የመጀመሪያ እና የአባት ስምዎን** ያስገቡ፦")
    await state.set_state(Registration.name)
    await callback_query.answer()

@dp.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("📱 አሁን ደግሞ **የስልክ ቁጥርዎን** ያስገቡ፦")
    await state.set_state(Registration.phone)

@dp.message(Registration.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("🏢 የሚማሩበትን **ዲፓርትመንት** ያስገቡ፦")
    await state.set_state(Registration.dept)

@dp.message(Registration.dept)
async def process_dept(message: Message, state: FSMContext):
    await state.update_data(department=message.text)
    sex_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ወንድ (Male)", callback_data="sex_male"),
         InlineKeyboardButton(text="ሴት (Female)", callback_data="sex_female")]
    ])
    await message.answer("⚧ **ጾታዎን** ይምረጡ፦", reply_markup=sex_kb)
    await state.set_state(Registration.sex)

@dp.callback_query(Registration.sex)
async def process_sex(callback_query: CallbackQuery, state: FSMContext):
    sex_val = callback_query.data.replace("sex_", "")
    await state.update_data(sex=sex_val)
    year_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1ኛ ዓመት", callback_data="yr_1"), InlineKeyboardButton(text="2ኛ ዓመት", callback_data="yr_2")],
        [InlineKeyboardButton(text="3ኛ ዓመት", callback_data="yr_3"), InlineKeyboardButton(text="4ኛ ዓመት", callback_data="yr_4")],
        [InlineKeyboardButton(text="5ኛ ዓመት እና ከዚያ በላይ", callback_data="yr_5+")]
    ])
    await callback_query.message.edit_text("🎓 ስንተኛ ዓመት (Year) ተማሪ ነዎት? ይምረጡ፦", reply_markup=year_kb)
    await state.set_state(Registration.year)

@dp.callback_query(Registration.year)
async def process_year(callback_query: CallbackQuery, state: FSMContext):
    year_mapped = callback_query.data.replace("yr_", "")
    await state.update_data(year=year_mapped)
    campus_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Campus", callback_data="cp_Main"), 
         InlineKeyboardButton(text="🌿 Semera Campus", callback_data="cp_Semera")]
    ])
    await callback_query.message.edit_text("📍 የሚማሩበትን **ካምፓስ** ይምረጡ፦", reply_markup=campus_kb)
    await state.set_state(Registration.campus)

@dp.callback_query(Registration.campus)
async def process_campus(callback_query: CallbackQuery, state: FSMContext):
    campus_mapped = callback_query.data.replace("cp_", "")
    user_data = await state.get_data()
    chat_id = callback_query.message.chat.id
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "register_student",
                "chat_id": chat_id,
                "full_name": user_data['full_name'],
                "sex": user_data['sex'],
                "department": user_data['department'],
                "phone": user_data['phone'],
                "year": user_data['year'],
                "campus": campus_mapped
            }
            await session.post(GOOGLE_SCRIPT_URL, json=payload)
    except Exception as e:
        logging.error(f"Sheet Sync Error: {e}")
    
    await callback_query.message.edit_text(text="🎉 **ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!**")
    await state.clear()

async def main():
    init_db()
    # Web server-ሩን በ Background አስነሳነው
    asyncio.create_task(start_web_server()) 
    # Bot-ውን በ Polling አስነሳነው
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
