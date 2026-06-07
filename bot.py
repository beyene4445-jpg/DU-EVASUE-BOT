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

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (chat_id INTEGER PRIMARY KEY, full_name TEXT, sex TEXT, phone TEXT, department TEXT, year TEXT, campus TEXT, team TEXT)')
    conn.commit()
    conn.close()

# --- FSM STATES ---
class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    sex = State()
    year = State()
    campus = State()

# --- MENU LAYOUT ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 ለመመዝገብ (Register)", callback_data="menu_register")],
        [
            InlineKeyboardButton(text="👥 Teams", callback_data="menu_teams"),
            InlineKeyboardButton(text="📖 Daily Bible Life", callback_data="menu_bible")
        ],
        [
            InlineKeyboardButton(text="ℹ️ About us", callback_data="menu_about"),
            InlineKeyboardButton(text="📅 Program & Support", callback_data="menu_program")
        ]
    ])

# --- HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("እንኳን ወደ DUEVASUE FELLOWSHIP BOT በደህና መጡ! ✨", reply_markup=get_main_menu())

@dp.callback_query(F.data == "go_home")
async def go_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("እንኳን ወደ DUEVASUE FELLOWSHIP BOT በደህና መጡ! ✨", reply_markup=get_main_menu())

# --- NEW HANDLERS (Bible, About, Program) ---
@dp.callback_query(F.data == "menu_bible")
async def show_bible(callback: CallbackQuery):
    await callback.message.edit_text("📖 **Daily Bible Life**\n\nዕለታዊ የመጽሐፍ ቅዱስ ንባብ እና ማሰላሰያ ፕሮግራሞችን እዚህ ያገኛሉ።\n\n(ይህንን ክፍል ከቦቱ አስተዳዳሪ ጋር በመወያየት መሙላት ይችላሉ።)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]))

@dp.callback_query(F.data == "menu_about")
async def show_about(callback: CallbackQuery):
    await callback.message.edit_text("ℹ️ **About Us**\n\nዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት (DUEVASUE)።\n\nዓላማችን፡ ተማሪዎችን በመንፈሳዊ ህይወት ማነጽ ነው።", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]))

@dp.callback_query(F.data == "menu_program")
async def show_program(callback: CallbackQuery):
    await callback.message.edit_text("📅 **Program & Support**\n\nየህብረታችን ሳምንታዊ መርሃግብሮች እና የድጋፍ አገልግሎቶች።\n\n(እዚህ የፕሮግራም ዝርዝሩን መፃፍ ይችላሉ።)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]))

# --- TEAM HANDLERS ---
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
        conn = sqlite3.connect("duevasue.db")
        conn.execute('UPDATE students SET team = ? WHERE chat_id = ?', (TEAMS_DATA[team_code]["name"], chat_id))
        conn.commit()
        conn.close()
        await callback.message.edit_text(f"✅ እንኳን ደስ አለዎት! በ**{TEAMS_DATA[team_code]['name']}** ተመዝግበዋል።", reply_markup=get_main_menu())

# --- REGISTRATION HANDLERS ---
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
    await msg.answer("⚧ ጾታዎን ይምረጡ፦", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="ወንድ", callback_data="sex_m"), InlineKeyboardButton(text="ሴት", callback_data="sex_f")]]))
    await state.set_state(Registration.sex)

@dp.callback_query(Registration.sex)
async def proc_sex(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sex=callback.data)
    await callback.message.edit_text("🎓 ዓመትዎን ይምረጡ (1-5+):", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1", callback_data="yr_1"), InlineKeyboardButton(text="2", callback_data="yr_2")], [InlineKeyboardButton(text="3", callback_data="yr_3"), InlineKeyboardButton(text="4", callback_data="yr_4")], [InlineKeyboardButton(text="5+", callback_data="yr_5")]]))
    await state.set_state(Registration.year)

@dp.callback_query(Registration.year)
async def proc_year(callback: CallbackQuery, state: FSMContext):
    await state.update_data(year=callback.data)
    await callback.message.edit_text("📍 ካምፓስ ይምረጡ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Main", callback_data="camp_Main"), InlineKeyboardButton(text="Semera", callback_data="camp_Semera")]]))
    await state.set_state(Registration.campus)

@dp.callback_query(Registration.campus)
async def proc_campus(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    team_name = TEAMS_DATA.get(user_data.get("chosen_team"), {}).get("name", "ምንም")
    campus_val = callback.data.split("_")[1]
    
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?)', 
                   (callback.message.chat.id, user_data['name'], user_data['sex'], user_data['phone'], user_data['dept'], user_data['year'], campus_val, team_name))
    conn.commit()
    conn.close()

    admin_message = (
        f"🔔 **አዲስ የተመዘገበ ተማሪ**\n\n"
        f"👤 ስም: {user_data['name']}\n"
        f"⚧ ጾታ: {user_data['sex']}\n"
        f"📱 ስልክ: {user_data['phone']}\n"
        f"🏢 ዲፓርትመንት: {user_data['dept']}\n"
        f"🎓 ዓመት: {user_data['year']}\n"
        f"📍 ካምፓስ: {campus_val}\n"
        f"🛠 የተመደበበት ቲም: {team_name}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"አድሚን ጋር መልእክት ለመላክ አልተቻለም: {e}")
    
    await callback.message.edit_text(f"🎉 **ምዝገባው ተጠናቋል!**\n\nቲም፦ {team_name}", reply_markup=get_main_menu())
    await state.clear()

async def start_web_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

async def main():
    init_db()
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
