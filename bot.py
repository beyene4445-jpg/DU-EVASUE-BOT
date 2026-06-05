import os
import logging
import sqlite3
import asyncio
import aiohttp # ለ Google Sheets ግንኙነት
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

BOT_TOKEN = "8344884558:AAGnQyxzYUnKJYgaT-gQQ2Twv6xzr8wLGnA"
ADMIN_CHAT_ID = 6120164042
# እዚህ ጋር ያገኘኸውን የ Google Web App URL አስገባ
# አሮጌው (ይህን አጥፋው)
# GOOGLE_SCRIPT_URL = "YOUR_GOOGLE_SCRIPT_URL_HERE" 

# አዲሱ (ይህንን ለጥፍበት)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLy09Ie2igKzBhN6kPnYYHTO4QN2Si2AM3jRvFAgbjced91CepsdJdkGMEQv4uuQF9Yg/exec"
" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. የዳታቤዝ መዋቅር
def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            department TEXT,
            year TEXT,
            campus TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_registrations (
            chat_id INTEGER,
            team_name TEXT,
            PRIMARY KEY (chat_id, team_name)
        )
    ''')
    conn.commit()
    conn.close()

# 11ዱ የህብረቱ የአገልግሎት ክፍሎች (Teams) ዳታ
TEAMS_DATA = {
    "Prayer": {"name": "🙏 የጸሎት ቡድን (PRAY MOBILIZER)", "desc": "ይህ የጸሎት ቲም በፌሎሺፓችን ስለ ግል ህይወታችን፣ ስለ ሌሎች፣ ስለ ህብረታችን እና ስለ ሀገራችን የሚጸለይበት እንዲሁም የተለያዩ የጸሎት መርሃግብሮችን በማዘጋጀት ሌሎችን ለጸሎት የማስተባበርን አገልግሎት ያከናውናል።\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"},
    "Counseling": {"name": "🧠 የማማከር አገልግሎት (Guidance & Counseling)", "desc": "ይህ ቲም ክርስቲያን ተማሪዎችን በመንፈሳዊ፣ በማህበራዊ፣ በሥነ-ልቦናዊ እና ትምህርታዊ ጉዳዮች ዙሪያ የምክክር አገልግሎት ይፈጽማል፣ ይጸልያል፣ ይከታተላል።\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"},
    "Teaching": {"name": "📖 ትምህርት እና ስልጠና (Teaching & Training)", "desc": "ይህ ቲም ተማሪዎች በመንፈሳዊ ሕይወት እንዲያድጉ አስፈላጊዉን ትምህርት እና ስልጠና ያዘጋጃል፣ ይሰጣል፡፡ በሕብረቱ ውስጥ ያሉትን የመጽሐፍ ቅዱስ ቡድኖች ያደራጃል፣ በጥናት ወቅትም ይከታተላል።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"},
    "Evan": {"name": "🔥 EVAN Mobilizer (የወንጌል ስርጭት)", "desc": "ዋና ትኩረቱን የወንጌል ምስክርነት ላይ በማድረግ ግቢ ውስጥ ላሉ ላልዳኑ ነፍሳት ወንጌልን መመስከር፣ ሌሎችን ለወንጌል ምስክርነት ማነሳሳት፣ በየጊዜው ከግቢ ውጭ ባሉ አካባቢዎች የወንጌል ስርጭት ማከናወን (Outreach, MiniMission, BreakMission)።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"},
    "Worship": {"name": "🎵 የአምልኮ ቡድን (WORSHIP TEAM)", "desc": "ሕብረቱ ባሉት የአምልኮ ፕሮግራሞች ላይ በመዝሙር የአምልኮ ፕሮግራሙን ይመራል። አዳዲስ መዝሙሮችን ይለቃል፣ የዝማሬ እና የልምምድ መርሃግብሮችን ያከናውናል።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"},
    "Love": {"name": "🤝 ፍቅርና የርህራሄ አገልግሎት (Love Sharing)", "desc": "በተለያዩ ጉዳዮች ቁሳዊ እንዲሁም ስነልቦናዊ ድጋፍ ለሚያስፈልጋቸው ተማሪዎች የድጋፍ አገልግሎትን ይሰጣል። በሆስፒታሎች፣ በማረሚያ ቤቶች የሚገኙ ሰዎችን እና አቅም ያጡ አረጋዊያንን መጎብኘት፣ የደም ልገሳ መርሃግብሮችን ማከናወን ዋና ተግባሩ ነው።\n\n📅 **የቲም ቀን፦** ዘወትር እሮብ ከ 11:00 - 1:30"},
    "Art": {"name": "🎭 ድራማ እና ስነጽሁፍ ህብረት (ART & Literature)", "desc": "መንፈሳዊ እና መጽሐፍ ቅዱሳዊ ይዘት ያላቸው ድራማ እና ፊልም፣ ግጥም፣ ትረካ እና ምሳሌዎችን ያዘጋጃል፣ በተለያዩ ልዩ ፕሮግራሞች ላይ ያቀርባል።\n\n📅 **የቲም ቀን፦** ዘወትር እሮብ ከ 11:00 - 1:30"},
    "Fund": {"name": "💰 FUNDRAISING (ገቢ አሰባሳቢ)", "desc": "ለሕብረቱ ገቢ ለማስገኘት ማንኛውንም አግባብ ያለው የፈጠራ ክህሎት በመጠቀም ለወንጌል ሥራ የሚሆን ገቢ ያሰባስባል፡፡\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"},
    "Natanim": {"name": "🧹 መስተንግዶ /ናታኒም/ (NATANIM TEAM)", "desc": "በሕብረቱ አገልግሎት ሰዎችን ማስተናገድ፣ መባ መሰብሰብ፣ በስጦታ ፕሮግራሞች ስጦታዎችን መቀበል እና የፅዳት ተግባራትን ያከናውናል። የሕብረቱን ንብረት በኃላፊነት ይረከባል፣ ይቆጣጠራል።\n\n📅 **የቲም ቀን፦** ዘወትር ቅዳሜ ከ 11:00 - 1:30"},
    "Choir": {"name": "🎤 የመዘምራን ቡድን (Choir Team)", "desc": "አዳዲስ ዝማሬዎችን በማዘጋጀት ለሕብረቱ መደበኛ እና ልዩ ፕሮግራሞች ያቀርባሉ። በቲም ቀን የጸሎት እና የልምምድ መርሃግብሮችን ያከናውናሉ።\n\n📅 **የቲም ቀን፦** ዘወትር ቅዳሜ ከ 11:00 - 1:30"},
    "Media": {"name": "📱 የማህበራዊ ሚዲያ ህብረት (Digital Media)", "desc": "ስለ ፌሎሺፕ የተለያዩ ፕሮግራሞችን መስራት፣ ፎቶዎችንና ቪዲዮዎችን በማንሳት ማስታወሻ መያዝ እና ለህዝብ ማድረስ። ራዕዩ ማህበራዊ ሚዲያን በመጠቀም ወንጌልን ለትውልዱ ማድረስ ነው።"}
}

class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    year = State()
    campus = State()

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="🔐 የህብረቱ አባል መሆን (Register)", callback_data="menu_register")],
        [InlineKeyboardButton(text="ℹ️ ስለ ህብረቱ (About)", callback_data="menu_about"), 
         InlineKeyboardButton(text="👥 የአገልግሎት ክፍሎች (Teams)", callback_data="menu_teams")],
        [InlineKeyboardButton(text="📖 Daily Bible Life", callback_data="menu_bible"),
         InlineKeyboardButton(text="📅 ፕሮግራሞች / ድጋፍ (Programs)", callback_data="menu_programs")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ወደ ዋና ማውጫ ተመለስ", callback_data="go_to_main")]])

@dp.message(Command("start"))
async def start_command(message: Message):
    welcome_text = (
        "እንኳን ወደ ዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት (ECSF/DUEVASUE) ቦት በደህና መጡ! ✨\n\n"
        "“እግዚአብሔርን ፈልጉት ትጸናላችሁም፤ ሁልጊዜ ፊቱን ፈልጉ።” — መዝሙር 105፥4\n\n"
        "💻 **Developed by:** Petros Beyene\n\n"
        "እባክዎ ከታች ካሉት አማራጮች አንዱን በመምረጥ አገልግሎቱን ያግኙ፦"
    )
    await message.answer(text=welcome_text, reply_markup=get_main_menu())

@dp.callback_query(lambda c: c.data == "go_to_main")
async def back_to_main_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_text(text="እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፦", reply_markup=get_main_menu())

# --- Registration (Modified with Google Sheet Sync) ---
@dp.callback_query(lambda c: c.data == "menu_register")
async def start_registration(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("📝 **የተማሪዎች መረጃ መሰብሰቢያ ቅጽ**\n\nእባክዎ **የመጀመሪያ እና የአባት ስምዎን** ያስገቡ፦")
    await state.set_state(Registration.name)
    await callback_query.answer()

@dp.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("📱 እሺ! አሁን ደግሞ **የስልክ ቁጥርዎን** ያስገቡ፦")
    await state.set_state(Registration.phone)

@dp.message(Registration.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("🏢 እባክዎ የሚማሩበትን **ዲፓርትመንት (Department)** ያስገቡ፦")
    await state.set_state(Registration.dept)

@dp.message(Registration.dept)
async def process_dept(message: Message, state: FSMContext):
    await state.update_data(department=message.text)
    year_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1ኛ ዓመት", callback_data="yr_1"), InlineKeyboardButton(text="2ኛ ዓመት", callback_data="yr_2")],
        [InlineKeyboardButton(text="3ኛ ዓመት", callback_data="yr_3"), InlineKeyboardButton(text="4ኛ ዓመት", callback_data="yr_4")],
        [InlineKeyboardButton(text="5ኛ ዓመት እና ከዚያ በላይ", callback_data="yr_5+")]
    ])
    await message.answer("🎓 ስንተኛ ዓመት (Year) ተማሪ ነዎት? ይምረጡ፦", reply_markup=year_kb)
    await state.set_state(Registration.year)

@dp.callback_query(Registration.year)
async def process_year(callback_query: CallbackQuery, state: FSMContext):
    year_mapped = callback_query.data.replace("yr_", "")
    await state.update_data(year=year_mapped)
    campus_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Campus", callback_data="cp_Main"), 
         InlineKeyboardButton(text="🌿 Semera Campus", callback_data="cp_Semera")]
    ])
    await callback_query.message.edit_text("📍 የሚማሩበትን **ካምፓስ (Campus)** ይምረጡ፦", reply_markup=campus_kb)
    await state.set_state(Registration.campus)

@dp.callback_query(Registration.campus)
async def process_campus(callback_query: CallbackQuery, state: FSMContext):
    campus_mapped = callback_query.data.replace("cp_", "")
    await state.update_data(campus=campus_mapped)
    user_data = await state.get_data()
    chat_id = callback_query.message.chat.id
    
    # 1. Save to DB
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO students (chat_id, full_name, phone, department, year, campus)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, user_data['full_name'], user_data['phone'], user_data['department'], user_data['year'], campus_mapped))
    conn.commit()
    conn.close()
    
    # 2. Sync to Google Sheets
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "register_student",
                "chat_id": chat_id,
                "full_name": user_data['full_name'],
                "phone": user_data['phone'],
                "department": user_data['department'],
                "year": user_data['year'],
                "campus": campus_mapped
            }
            await session.post(GOOGLE_SCRIPT_URL, json=payload)
    except Exception as e:
        logging.error(f"Sheet Sync Error: {e}")
    
    success_text = "🎉 **ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!** 🎉\n\nመረጃዎ በህብረቱ ዳታቤዝ እና በGoogle Sheet ላይ ተቀምጧል።"
    await callback_query.message.edit_text(text=success_text, reply_markup=get_back_keyboard())
    await state.clear()

# --- Teams & Programs ---
@dp.callback_query(lambda c: c.data == "menu_teams")
async def teams_menu_handler(callback_query: CallbackQuery):
    keyboard = []
    row = []
    for code, data in TEAMS_DATA.items():
        row.append(InlineKeyboardButton(text=data["name"].split("(")[0].strip(), callback_data=f"view_team_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="⬅️ ወደ ዋና ማውጫ", callback_data="go_to_main")])
    await callback_query.message.edit_text(text="👥 **የአገልግሎት ዘርፍ ምርጫ**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(lambda c: c.data.startswith("view_team_"))
async def view_team_detail_handler(callback_query: CallbackQuery):
    team_code = callback_query.data.replace("view_team_", "")
    team = TEAMS_DATA.get(team_code)
    if not team: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ አሁን ተመዝገብ", callback_data=f"confirm_join_{team_code}")],
        [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="menu_teams")]
    ])
    await callback_query.message.edit_text(text=f"🔹 **{team['name']}**\n\n{team['desc']}", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("confirm_join_"))
async def confirm_join_team_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    team_code = callback_query.data.replace("confirm_join_", "")
    team_name = TEAMS_DATA[team_code]["name"]
    
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO team_registrations (chat_id, team_name) VALUES (?, ?)', (chat_id, team_name))
        conn.commit()
        
        # Sync to Google Sheets
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(GOOGLE_SCRIPT_URL, json={"action": "join_team", "chat_id": chat_id, "team_name": team_name})
        except: pass
        
        msg = f"✅ በ**{team_name}** ተመዝግበዋል!"
    except sqlite3.IntegrityError:
        msg = f"⚠️ ቀድሞ ተመዝግበዋል።"
    finally:
        conn.close()
    await callback_query.message.answer(text=msg, parse_mode="Markdown")
    await callback_query.answer()

# --- Helpers ---
@dp.callback_query(lambda c: c.data == "menu_about")
async def about_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(text="📌 **ስለ ህብረቱ**\n...", reply_markup=get_back_keyboard())

@dp.callback_query(lambda c: c.data == "menu_programs")
async def programs_and_support_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(text="📅 **ፕሮግራሞች**\n...", reply_markup=get_back_keyboard(), parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "menu_bible")
async def bible_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(text="📖 **Daily Bible Life**\n...", reply_markup=get_back_keyboard())

async def handle_render(request):
    return web.Response(text="DUEVASUE Bot Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

async def main():
    init_db()
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
