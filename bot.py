import os
import logging
import sqlite3
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
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

# --- Teams Data ---
TEAMS_DATA = {
    "Prayer": {"name": "🙏 የጸሎት ቡድን (PRAY MOBILIZER)", "desc": "የጸሎት መርሃግብሮችን በማዘጋጀት ሌሎችን ለጸሎት የማስተባበር አገልግሎት።\n📅 ሰኞ 11:00 - 1:30"},
    "Counseling": {"name": "🧠 የማማከር አገልግሎት", "desc": "መንፈሳዊ፣ ማህበራዊ እና ትምህርታዊ የምክክር አገልግሎት።\n📅 ሰኞ 11:00 - 1:30"},
    "Teaching": {"name": "📖 ትምህርት እና ስልጠና", "desc": "መንፈሳዊ ስልጠና እና የመጽሐፍ ቅዱስ ቡድኖችን ማደራጀት።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Evan": {"name": "🔥 EVAN Mobilizer", "desc": "ወንጌልን መመስከር፣ Outreach እና MiniMission ማከናወን።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Worship": {"name": "🎵 የአምልኮ ቡድን", "desc": "በመዝሙር የአምልኮ ፕሮግራሞችን መምራት።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Love": {"name": "🤝 ፍቅርና የርህራሄ አገልግሎት", "desc": "ለተቸገሩ ድጋፍ ማድረግ፣ የደም ልገሳ እና የሆስፒታል ጉብኝት።\n📅 እሮብ 11:00 - 1:30"},
    "Art": {"name": "🎭 ድራማ እና ስነጽሁፍ", "desc": "መንፈሳዊ ድራማ፣ ግጥም እና ትረካዎችን ማዘጋጀት።\n📅 እሮብ 11:00 - 1:30"},
    "Fund": {"name": "💰 FUNDRAISING", "desc": "ለወንጌል ሥራ የሚሆን ገቢ ማሰባሰብ።\n📅 ሰኞ 11:00 - 1:30"},
    "Natanim": {"name": "🧹 መስተንግዶ /ናታኒም/", "desc": "ሰዎችን ማስተናገድ፣ መባ መሰብሰብ እና ንብረት መጠበቅ።\n📅 ቅዳሜ 11:00 - 1:30"},
    "Choir": {"name": "🎤 የመዘምራን ቡድን", "desc": "አዳዲስ ዝማሬዎችን ማዘጋጀት።\n📅 ቅዳሜ 11:00 - 1:30"},
    "Media": {"name": "📱 የማህበራዊ ሚዲያ ህብረት", "desc": "ፎቶ፣ ቪዲዮ እና የዲጂታል ሚዲያ አገልግሎት።"}
}

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (chat_id INTEGER PRIMARY KEY, full_name TEXT, sex TEXT, phone TEXT, department TEXT, year TEXT, campus TEXT)''')
    conn.commit()
    conn.close()

# --- Web Server for Render ---
async def handle_render(request):
    return web.Response(text="DUEVASUE Bot Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    sex = State()
    year = State()
    campus = State()

# --- Keyboards ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 ምዝገባ (Register)", callback_data="menu_register")],
        [InlineKeyboardButton(text="ℹ️ ስለ ህብረቱ", callback_data="menu_about"), 
         InlineKeyboardButton(text="👥 የአገልግሎት ክፍሎች", callback_data="menu_teams")],
        [InlineKeyboardButton(text="📅 ፕሮግራሞች", callback_data="menu_programs"),
         InlineKeyboardButton(text="📖 Daily Bible Life", callback_data="menu_bible")]
    ])

def get_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ወደ ዋናው ሜኑ", callback_data="go_home")]])

# --- Handlers ---
@dp.message(Command("start"))
async def start_command(message: Message):
    text = ("እንኳን ወደ ዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት ቦት በደህና መጡ! ✨\n\n"
            "“እግዚአብሔርን ፈልጉት ትጸናላችሁም፤ ሁልጊዜ ፊቱን ፈልጉ።” — መዝሙር 105፥4")
    await message.answer(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "go_home")
async def go_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፦", reply_markup=get_main_menu())

# --- Registration Flow ---
@dp.callback_query(F.data == "menu_register")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 **የስም መመዝገቢያ**\nእባክዎ ስምዎን ያስገቡ፦")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def proc_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📱 የስልክ ቁጥር ያስገቡ፦")
    await state.set_state(Registration.phone)

@dp.message(Registration.phone)
async def proc_phone(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await msg.answer("🏢 ዲፓርትመንት ያስገቡ፦")
    await state.set_state(Registration.dept)

@dp.message(Registration.dept)
async def proc_dept(msg: Message, state: FSMContext):
    await state.update_data(dept=msg.text)
    await msg.answer("⚧ ጾታዎን ይምረጡ፦", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ወንድ", callback_data="s_m"), InlineKeyboardButton(text="ሴት", callback_data="s_f")]]))
    await state.set_state(Registration.sex)

@dp.callback_query(Registration.sex)
async def proc_sex(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sex=callback.data)
    await callback.message.edit_text("🎓 ዓመትዎን ይምረጡ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="y_1"), InlineKeyboardButton(text="2", callback_data="y_2")],
        [InlineKeyboardButton(text="3", callback_data="y_3"), InlineKeyboardButton(text="4", callback_data="y_4"), InlineKeyboardButton(text="5+", callback_data="y_5")]]))
    await state.set_state(Registration.year)

@dp.callback_query(Registration.year)
async def proc_year(callback: CallbackQuery, state: FSMContext):
    await state.update_data(year=callback.data)
    await callback.message.edit_text("📍 ካምፓስ ይምረጡ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Main", callback_data="c_Main"), InlineKeyboardButton(text="Semera", callback_data="c_Semera")]]))
    await state.set_state(Registration.campus)

@dp.callback_query(Registration.campus)
async def proc_campus(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    chat_id = callback.message.chat.id
    
    # 1. Save to DB
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?)', 
                   (chat_id, user_data['name'], user_data['sex'], user_data['phone'], user_data['dept'], user_data['year'], callback.data))
    conn.commit()
    conn.close()

    # 2. Sync to Google Sheets
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"action": "register", "name": user_data['name'], "phone": user_data['phone'], "campus": callback.data}
            await session.post(GOOGLE_SCRIPT_URL, json=payload)
    except: pass
    
    await callback.message.edit_text("🎉 **ምዝገባው ተጠናቋል!**", reply_markup=get_main_menu())
    await state.clear()

async def main():
    init_db()
    # Web server-ሩን አስነሳ
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
