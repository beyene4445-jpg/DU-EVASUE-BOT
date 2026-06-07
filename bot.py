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

# --- CONFIGURATION ---
BOT_TOKEN = "8344884558:AAGnQyxzYUnKJYgaT-gQQ2Twv6xzr8wLGnA"
ADMIN_CHAT_ID = "6120164042"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLy09Ie2igKzBhN6kPnYYHTO4QN2Si2AM3jRvFAgbjced91CepsdJdkGMEQv4uuQF9Yg/exec"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- TEAMS DATA ---
TEAMS_DATA = {
    "Prayer": {"name": "🙏 የጸሎት ቡድን", "desc": "የጸሎት መርሃግብሮችን በማዘጋጀት ሌሎችን ለጸሎት የማስተባበር አገልግሎት።\n📅 ሰኞ 11:00 - 1:30"},
    "Counseling": {"name": "🧠 የማማከር አገልግሎት", "desc": "መንፈሳዊ፣ ማህበራዊ እና ትምህርታዊ የምክክር አገልግሎት።\n📅 ሰኞ 11:00 - 1:30"},
    "Teaching": {"name": "📖 ትምህርት እና ስልጠና", "desc": "መንፈሳዊ ስልጠና እና የመጽሐፍ ቅዱስ ቡድኖችን ማደራጀት።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Evan": {"name": "🔥 EVAN Mobilizer", "desc": "ወንጌልን መመስከር፣ Outreach እና MiniMission ማከናወን።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Worship": {"name": "🎵 የአምልኮ ቡድን", "desc": "በመዝሙር የአምልኮ ፕሮግራሞችን መምራት።\n📅 ማክሰኞ 11:00 - 1:30"},
    "Love": {"name": "🤝 ፍቅርና የርህራሄ አገልግሎት", "desc": "ለተቸገሩ ድጋፍ ማድረግ፣ የደም ልገሳ እና የሆስፒታል ጉብኝት።\n📅 እሮብ 11:00 - 1:30"},
    "Art": {"name": "🎭 ድራማ እና ስነጽሁፍ", "desc": "መንፈሳዊ ድራማ፣ ግጥም እና ትረካዎችን ማዘጋጀት።\n📅 እሮብ 11:00 - 1:30"},
    "Fund": {"name": "💰 FUNDRAISING", "desc": "ለወንጌል ሥራ የሚሆን ገቢ ማሰባሰብ።\n📅 ሰኞ 11:00 - 1:30"},
    "Natanim": {"name": "🧹 መስተንግዶ /ናታኒም/", "desc": "ሰዎችን ማስተናገድ፣ መባ መሰብሰብ እና ንብረት መጠበቅ።\n📅 ቅዳሜ 11:00 - 1:30"},
    "Choir": {"name": "🎤 የመዘምራን ቡድን", "desc": "አዳዲስ ዝማሬዎችን ማዘጋጀት።\n📅 ቅዳሜ 11:00 - 1:30"},
    "Media": {"name": "📱 የማህበራዊ ሚዲያ", "desc": "ፎቶ፣ ቪዲዮ እና የዲጂታል ሚዲያ አገልግሎት።"}
}

# --- DATABASE & WEB SERVER ---
def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (chat_id INTEGER PRIMARY KEY, full_name TEXT, sex TEXT, phone TEXT, department TEXT, year TEXT, campus TEXT, team TEXT)')
    conn.commit()
    conn.close()

async def start_web_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

# --- FSM STATES ---
class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    sex = State()
    year = State()
    campus = State()

# --- UTILS ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 ምዝገባ", callback_data="menu_register")],
        [InlineKeyboardButton(text="👥 የአገልግሎት ክፍሎች", callback_data="menu_teams")],
        [InlineKeyboardButton(text="⬅️ ወደ ዋናው ገጽ", callback_data="go_home")]
    ])

# --- HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("እንኳን ወደ ዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት ቦት በደህና መጡ! ✨", reply_markup=get_main_menu())

@dp.callback_query(F.data == "go_home")
async def go_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፦", reply_markup=get_main_menu())

@dp.callback_query(F.data == "menu_teams")
async def show_teams(callback: CallbackQuery):
    kb = [[InlineKeyboardButton(text=data["name"], callback_data=f"view_{code}")] for code, data in TEAMS_DATA.items()]
    kb.append([InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")])
    await callback.message.edit_text("👥 **የአገልግሎት ዘርፎች**\nአንዱን ይምረጡ፦", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("view_"))
async def view_team(callback: CallbackQuery):
    code = callback.data.split("_")[1]
    team = TEAMS_DATA[code]
    kb = [[InlineKeyboardButton(text="✅ ይህንን ቲም ተቀላቀል", callback_data=f"join_{code}")], [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="menu_teams")]]
    await callback.message.edit_text(f"🔹 **{team['name']}**\n\n{team['desc']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("join_"))
async def join_team(callback: CallbackQuery, state: FSMContext):
    team_code = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    conn = sqlite3.connect("duevasue.db")
    user = conn.execute("SELECT * FROM students WHERE chat_id=?", (chat_id,)).fetchone()
    conn.close()

    if not user:
        await state.update_data(chosen_team=team_code)
        await callback.message.edit_text("ቲሙን ለመቀላቀል በመጀመሪያ መመዝገብ አለብዎት።\n\n📝 እባክዎ **የመጀመሪያ እና የአባት ስምዎን** ያስገቡ፦")
        await state.set_state(Registration.name)
    else:
        conn = sqlite
