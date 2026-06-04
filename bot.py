import os
import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# 1. አዲሱ የቦት ቶከን እና አድሚን ID
BOT_TOKEN = "8344884558:AAGnQyxzYUnKJYgaT-gQQ2Twv6xzr8wLGnA"
ADMIN_CHAT_ID = 6120164042

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 2. የ SQLite ዳታቤዝ መዋቅር ማዘጋጀት
def init_db():
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    # የተማሪዎች መረጃ ሰንጠረዥ
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
    # ለቲም ምዝገባ ሰንጠረዥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_registrations (
            chat_id INTEGER,
            team_name TEXT,
            PRIMARY KEY (chat_id, team_name)
        )
    ''')
    conn.commit()
    conn.close()

# 3. የምዝገባ ቅደም ተከተል ደረጃዎች (FSM States)
class Registration(StatesGroup):
    name = State()
    phone = State()
    dept = State()
    year = State()
    campus = State()

# 4. ዋና ማውጫ ቁልፎች (Main Menu Layout)
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="🔐 የህብረቱ አባል መሆን (Register)", callback_data="menu_register")],
        [InlineKeyboardButton(text="ℹ️ ስለ ህብረቱ (About)", callback_data="menu_about"), 
         InlineKeyboardButton(text="👥 የአገልግሎት ክፍሎች (Teams)", callback_data="menu_teams")],
        [InlineKeyboardButton(text="📖 Daily Bible Life", callback_data="menu_bible"),
         InlineKeyboardButton(text="📅 ፕሮግራሞች (Programs)", callback_data="menu_programs")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ⬅️ ወደ ዋና ማውጫ መመለሻ ቁልፍ
def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ ወደ ዋና ማውጫ ተመለስ", callback_data="go_to_main")]
    ])

# --- /start Command ---
@dp.message(Command("start"))
async def start_command(message: Message):
    welcome_text = (
        "እንኳን ወደ ዲላ ዩኒቨርሲቲ ክርስቲያን ተማሪዎች ህብረት (DUEVASUE/EVASUE) ቦት በደህና መጡ! ✨\n\n"
        "ይህ ቦት የህብረታችንን መረጃዎች የሚያገኙበት፣ ለአገልግሎት ክፍሎች የሚመዘገቡበት እና የዕለት ተዕለት የቃል ህይወትዎን የሚገመግሙበት ነውእ።\n\n"
        "━━━━━━━ ● ━━━━━━━\n"
        "💻 **Developed by:** Petros Beyene\n\n"
        "እባክዎ ከታች ካሉት አማራጮች አንዱን በመምረጥ አገልግሎቱን ያግኙ፦"
    )
    await message.answer(text=welcome_text, reply_markup=get_main_menu())

# --- ወደ ዋና ማውጫ መመለሻ Handlers ---
@dp.callback_query(lambda c: c.data == "go_to_main")
async def back_to_main_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear() # ማንኛውም የቀረ FSM ካለ ያጸዳዋል
    await callback_query.message.edit_text(text="እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፦", reply_markup=get_main_menu())

# --- 1. ስለ ህብረቱ (About) ---
@dp.callback_query(lambda c: c.data == "menu_about")
async def about_handler(callback_query: CallbackQuery):
    about_text = (
        "📌 **የ DUEVASUE / EVASUE ራዕይ፣ አላማ እና እሴቶች**\n\n"
        "🎯 **ራዕይ (Vision)፦** በካምፓስ ውስጥ በወንጌል የዳኑ፣ በቃል የበቁ እና ማህበረሰቡን በክርስቶስ ፍቅር የሚለውጡ ተማሪዎችን ማየት።\n\n"
        "📜 **አላማ (Mission)፦** ተማሪዎች በዩኒቨርሲቲ ቆይታቸው በክርስቶስ እውቀት እንዲያድጉ፣ በወንጌል ስራ እንዲተጉ እና ለነገዋ ቤተክርስቲያንና ሀገር ብቁ መሪ እንዲሆኑ ማዘጋጀት።\n\n"
        "💎 **እሴቶች (Core Values)፦** ፍቅር፣ ቅድስና፣ አንድነት፣ ታማኝነት፣ በቃል መበርታት እና ለወንጌል መቅናት።"
    )
    await callback_query.message.edit_text(text=about_text, reply_markup=get_back_keyboard())

# --- 2. የተማሪዎች ምዝገባ ሂደት (FSM Registration) ---
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
    
    # መረጃውን ወደ SQLite ዳታቤዝ ማስቀመጥ
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO students (chat_id, full_name, phone, department, year, campus)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, user_data['full_name'], user_data['phone'], user_data['department'], user_data['year'], user_data['campus']))
    conn.commit()
    conn.close()
    
    success_text = (
        "🎉 **ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!** 🎉\n\n"
        f"👤 **ስም፦** {user_data['full_name']}\n"
        f"📱 **ስልክ፦** {user_data['phone']}\n"
        f"🏢 **ዲፓርትመንት፦** {user_data['department']}\n"
        f"🎓 **ዓመት፦** {user_data['year']}\n"
        f"📍 **ካምፓስ፦** {user_data['campus']}\n\n"
        "መረጃዎ በህብረቱ ዳታቤዝ ውስጥ በሚገባ ተቀምጧል። ጌታ ይባርክዎ!"
    )
    
    await callback_query.message.edit_text(text=success_text, reply_markup=get_back_keyboard())
    await state.clear()

# --- 3. የአገልግሎት ክፍሎች (Teams) ---
@dp.callback_query(lambda c: c.data == "menu_teams")
async def teams_handler(callback_query: CallbackQuery):
    teams_text = (
        "👥 **የ DUEVASUE የክፍላት/ቲሞች አገልግሎት**\n\n"
        "በህብረታችን ውስጥ ያሉ ዋና ዋና የአገልግሎት ክፍሎች የሚከተሉት ናቸው፦\n"
        "• 🎤 **የመዘምራን ክፍል (Choir & Score)**\n"
        "• 🔥 **የወንጌል ስርጭትና ደቀመዝሙርነት ክፍል**\n"
        "• 🙏 **የጸሎትና የነገረ-መለኮት ክፍል**\n"
        "• 🤝 **የእርዳታና የማህበራዊ አገልግሎት ክፍል**\n"
        "• 📢 **የሚዲያ፣ ኮሚኒኬሽንና ስነ-ጽሁፍ ክፍል**\n\n"
        "ማሳሰቢያ፦ ወደ እነዚህ ክፍሎች ለመቀላቀልና ለመመዝገብ በቅርቡ ሙሉ የፎርም ሲስተም ይዘን እንቀርባለን!"
    )
    await callback_query.message.edit_text(text=teams_text, reply_markup=get_back_keyboard())

# --- 4. Daily Bible Life (መጽሐፍ ቅዱስ ንባብ ግምገማ) ---
@dp.callback_query(lambda c: c.data == "menu_bible")
async def bible_handler(callback_query: CallbackQuery):
    bible_text = (
        "📖 **Daily Bible Life (የዕለት ተዕለት የቃል ሕይወት)**\n\n"
        "“ሰው ከእግዚአብሔር አፍ በሚወጣ ቃል ሁሉ እንጂ በእንጀራ ብቻ አይኖርም ተብሎ ተጽፎአል።” — ማቴ 4:4\n\n"
        "ይህ ክፍል ተማሪዎች በየቀኑ ያነበቡትን የመጽሐፍ ቅዱስ ክፍል ሪፖርት የሚያደርጉበትና መንፈሳዊ ጉዟቸውን የሚገመግሙበት ነው።\n\n"
        "⚙️ *የዕለቱ የንባብ ማመሳከሪያና የቼክ-ኢን (Check-in) ሲስተም በቅርቡ ይዘመናል!*"
    )
    await callback_query.message.edit_text(text=bible_text, reply_markup=get_back_keyboard())

# --- 5. ፕሮግራሞች (Programs & Events) ---
@dp.callback_query(lambda c: c.data == "menu_programs")
async def programs_handler(callback_query: CallbackQuery):
    programs_text = (
        "📅 **የህብረቱ መደበኛ ሳምንታዊ ፕሮግራሞች**\n\n"
        "• ⛪ **የአርብ ምሽት አምልኮና ትምህርት፦** ከምሽቱ 11:30 - 2:00 (በዋናው ግቢ ግቢ ጉባኤ)\n"
        "• ☀️ **የእሁድ ጠዋት ታላቅ አምልኮ፦** ከጠዋቱ 2:30 - 6:00\n"
        "• 🙏 **የእለት ተእለት የጸሎት ፕሮግራም፦** በየቀኑ ማለዳ 12:00 - 1:00\n"
        "• 📖 **የዶርም መጽሐፍ ቅዱስ ጥናት፦** በየሳምንቱ በየክፍሉ የሚሰጥ\n\n"
        "📌 ልዩ ኮንፈረንሶች እና የእንግዳ መጋቢዎች ፕሮግራም ሲኖር በዚህ ገጽ ላይ ይፋ ይደረጋል!"
    )
    await callback_query.message.edit_text(text=programs_text, reply_markup=get_back_keyboard())

# --- ለኢንተርኔት ሰርቨር (Render Webhook/Ping) ---
async def handle_render(request):
    return web.Response(text="DUEVASUE Fellowship Bot is Running Perfect with New Token!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    init_db() # ቦቱ ሲነሳ ዳታቤዙን በራሱ ጊዜ ይፈጥራል
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
