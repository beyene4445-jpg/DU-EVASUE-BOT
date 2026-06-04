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

BOT_TOKEN = "8344884558:AAGnQyxzYUnKJYgaT-gQQ2Twv6xzr8wLGnA"
ADMIN_CHAT_ID = 6120164042

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. የዳታቤዝ መዋቅር (የተማሪዎች እና የቲም ምዝገባ)
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
    "Prayer": {
        "name": "🙏 የጸሎት ቡድን (PRAY MOBILIZER)",
        "desc": "ይህ የጸሎት ቲም በፌሎሺፓችን ስለ ግል ህይወታችን፣ ስለ ሌሎች፣ ስለ ህብረታችን እና ስለ ሀገራችን የሚጸለይበት እንዲሁም የተለያዩ የጸሎት መርሃግብሮችን በማዘጋጀት ሌሎችን ለጸሎት የማስተባበርን አገልግሎት ያከናውናል።\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"
    },
    "Counseling": {
        "name": "🧠 የማማከር አገልግሎት (Guidance & Counseling)",
        "desc": "ይህ ቲም ክርስቲያን ተማሪዎችን በመንፈሳዊ፣ በማህበራዊ፣ በሥነ-ልቦናዊ እና ትምህርታዊ ጉዳዮች ዙሪያ የምክክር አገልግሎት ይፈጽማል፣ ይጸልያል፣ ይከታተላል።\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"
    },
    "Teaching": {
        "name": "📖 ትምህርት እና ስልጠና (Teaching & Training)",
        "desc": "ይህ ቲም ተማሪዎች በመንፈሳዊ ሕይወት እንዲያድጉ አስፈላጊዉን ትምህርት እና ስልጠና ያዘጋጃል፣ ይሰጣል፡፡ በሕብረቱ ውስጥ ያሉትን የመጽሐፍ ቅዱስ ቡድኖች ያደራጃል፣ በጥናት ወቅትም ይከታተላል።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"
    },
    "Evan": {
        "name": "🔥 EVAN Mobilizer (የወንጌል ስርጭት)",
        "desc": "ዋና ትኩረቱን የወንጌል ምስክርነት ላይ በማድረግ ግቢ ውስጥ ላሉ ላልዳኑ ነፍሳት ወንጌልን መመስከር፣ ሌሎችን ለወንጌል ምስክርነት ማነሳሳት፣ በየጊዜው ከግቢ ውጭ ባሉ አካባቢዎች የወንጌል ስርጭት ማከናወን (Outreach, MiniMission, BreakMission)።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"
    },
    "Worship": {
        "name": "🎵 የአምልኮ ቡድን (WORSHIP TEAM)",
        "desc": "ሕብረቱ ባሉት የአምልኮ ፕሮግራሞች ላይ በመዝሙር የአምልኮ ፕሮግራሙን ይመራል። አዳዲስ መዝሙሮችን ይለቃል፣ የዝማሬ እና የልምምድ መርሃግብሮችን ያከናውናል።\n\n📅 **የቲም ቀን፦** ዘወትር ማክሰኞ ከ 11:00 - 1:30"
    },
    "Love": {
        "name": "🤝 ፍቅርና የርህራሄ አገልግሎት (Love Sharing)",
        "desc": "በተለያዩ ጉዳዮች ቁሳዊ እንዲሁም ስነልቦናዊ ድጋፍ ለሚያስፈልጋቸው ተማሪዎች የድጋፍ አገልግሎትን ይሰጣል። በሆስፒታሎች፣ በማረሚያ ቤቶች የሚገኙ ሰዎችን እና አቅም ያጡ አረጋዊያንን መጎብኘት፣ የደም ልገሳ መርሃግብሮችን ማከናወን ዋና ተግባሩ ነው።\n\n📅 **የቲም ቀን፦** ዘወትር እሮብ ከ 11:00 - 1:30"
    },
    "Art": {
        "name": "🎭 ድራማ እና ስነጽሁፍ ህብረት (ART & Literature)",
        "desc": "መንፈሳዊ እና መጽሐፍ ቅዱሳዊ ይዘት ያላቸው ድራማ እና ፊልም፣ ግጥም፣ ትረካ እና ምሳሌዎችን ያዘጋጃል፣ በተለያዩ ልዩ ፕሮግራሞች ላይ ያቀርባል።\n\n📅 **የቲም ቀን፦** ዘወትር እሮብ ከ 11:00 - 1:30"
    },
    "Fund": {
        "name": "💰 FUNDRAISING (ገቢ አሰባሳቢ)",
        "desc": "ለሕብረቱ ገቢ ለማስገኘት ማንኛውንም አግባብ ያለው የፈጠራ ክህሎት በመጠቀም ለወንጌል ሥራ የሚሆን ገቢ ያሰባስባል፡፡\n\n📅 **የቲም ቀን፦** ዘወትር ሰኞ ከ 11:00 - 1:30"
    },
    "Natanim": {
        "name": "🧹 መስተንግዶ /ናታኒም/ (NATANIM TEAM)",
        "desc": "በሕብረቱ አገልግሎት ሰዎችን ማስተናገድ፣ መባ መሰብሰብ፣ በስጦታ ፕሮግራሞች ስጦታዎችን መቀበል እና የፅዳት ተግባራትን ያከናውናል። የሕብረቱን ንብረት በኃላፊነት ይረከባል፣ ይቆጣጠራል።\n\n📅 **የቲም ቀን፦** ዘወትር ቅዳሜ ከ 11:00 - 1:30"
    },
    "Choir": {
        "name": "🎤 የመዘምራን ቡድን (Choir Team)",
        "desc": "አዳዲስ ዝማሬዎችን በማዘጋጀት ለሕብረቱ መደበኛ እና ልዩ ፕሮግራሞች ያቀርባሉ። በቲም ቀን የጸሎት እና የልምምድ መርሃግብሮችን ያከናውናሉ።\n\n📅 **የቲም ቀን፦** ዘወትር ቅዳሜ ከ 11:00 - 1:30"
    },
    "Media": {
        "name": "📱 የማህበራዊ ሚዲያ ህብረት (Digital Media)",
        "desc": "ስለ ፌሎሺፕ የተለያዩ ፕሮግራሞችን መስራት፣ ፎቶዎችንና ቪዲዮዎችን በማንሳት ማስታወሻ መያዝ እና ለህዝብ ማድረስ። ራዕዩ ማህበራዊ ሚዲያን በመጠቀም ወንጌልን ለትውልዱ ማድረስ ነው።"
    }
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
        "🏠 *“Fellowship ለእኛ ምንጊዜም ቤታችን ነው”*\n\n"
        "━━━━━━━ ● ━━━━━━━\n"
        "💻 **Developed by:** Petros Beyene\n\n"
        "እባክዎ ከታች ካሉት አማራጮች አንዱን በመምረጥ አገልግሎቱን ያግኙ፦"
    )
    await message.answer(text=welcome_text, reply_markup=get_main_menu())

@dp.callback_query(lambda c: c.data == "go_to_main")
async def back_to_main_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.edit_text(text="እባክዎ ከታች ካሉት አማራጮች አንዱን ይምረጡ፦", reply_markup=get_main_menu())

# --- 1. ስለ ህብረቱ (About) ---
@dp.callback_query(lambda c: c.data == "menu_about")
async def about_handler(callback_query: CallbackQuery):
    about_text = (
        "📌 **የ DUEVASUE / ECSF ራዕይ፣ አላማ እና እሴቶች**\n\n"
        "🎯 **ራዕይ (Vision)፦** በካምፓስ ውስጥ በወንጌል የዳኑ፣ በቃል የበቁ እና ማህበረሰቡን በክርስቶስ ፍቅር የሚለውጡ ተማሪዎችን ማየት።\n\n"
        "📍 **መመሪያ ቃላት፦** #በመመለስ (Return) | #በፅድቅ_ኑሮ (Righteous Life) | #በመታመን (Trust)\n\n"
        "☎️ **የህብረቱ መሪዎች ስልክ ቁጥር፦**\n"
        "♦️ ሜቲ፦ 0945899064\n"
        "♦️ ፍቃዱ፦ 0987926081\n"
        "♦️ አድነዉ፦ 0916733651\n"
        "♦️ ማስረሻ፦ 0961819382\n"
        "♦️ ዲቦራ፦ 0979328380\n"
        "♦️ ተስፋጽዮን፦ 0983708869\n"
        "♦️ ሲሳይ፦ +251961130694"
    )
    await callback_query.message.edit_text(text=about_text, reply_markup=get_back_keyboard())

# --- 2. የተማሪዎች ምዝገባ (FSM) ---
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

# --- 3. የአገልግሎት ክፍሎች (Teams Main Menu) ---
@dp.callback_query(lambda c: c.data == "menu_teams")
async def teams_menu_handler(callback_query: CallbackQuery):
    keyboard = []
    # 11ዱን ቲሞች በተን በየመስመሩ 2 እያደረግን እንሰራለን
    row = []
    for code, data in TEAMS_DATA.items():
        row.append(InlineKeyboardButton(text=data["name"].split("(")[0].strip(), callback_data=f"view_team_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="⬅️ ወደ ዋና ማውጫ", callback_data="go_to_main")])
    
    await callback_query.message.edit_text(
        text="👥 **የአገልግሎት ዘርፍ ምርጫ**\n\nለሚቀጥሉት ዓመታት በፌሎሺፓችን ውስጥ የሚያገለግሉበትን የቲም ዝርዝር ለማየት እና ለመመዝገብ ከታች ካሉት አንዱን ይጫኑ፦",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# የአንድን ቲም ዝርዝር ማሳያ (View Team Detail)
@dp.callback_query(lambda c: c.data.startswith("view_team_"))
async def view_team_detail_handler(callback_query: CallbackQuery):
    team_code = callback_query.data.replace("view_team_", "")
    team = TEAMS_DATA.get(team_code)
    
    if not team:
        return
        
    detail_text = f"🔹 **{team['name']}**\n\n{team['desc']}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ በዚህ ቲም ላይ አሁን ተመዝገብ", callback_data=f"confirm_join_{team_code}")],
        [InlineKeyboardButton(text="⬅️ ወደ ቲሞች ዝርዝር ተመለስ", callback_data="menu_teams")]
    ])
    await callback_query.message.edit_text(text=detail_text, reply_markup=kb, parse_mode="Markdown")

# የቲም ምዝገባ ማረጋገጫ (Confirm Join Team)
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
        msg = f"✅ **በተሳካ ሁኔታ ተመዝግበዋል!**\n\nበ**{team_name}** ውስጥ ለማገልገል ያደረጉት ምርጫ ተመዝግቧል። የክፍሉ አስተባባሪዎች በቅርቡ ያገኙዎታል።"
    except sqlite3.IntegrityError:
        msg = f"⚠️ **አስቀድመው ተመዝግበዋል!**\n\nእርስዎ ቀድመው በ**{team_name}** ክፍል ውስጥ ተመዝግበዋል።"
    finally:
        conn.close()
        
    await callback_query.message.answer(text=msg, parse_mode="Markdown")
    await callback_query.answer()

# --- 4. Programs & Financial Support ---
@dp.callback_query(lambda c: c.data == "menu_programs")
async def programs_and_support_handler(callback_query: CallbackQuery):
    text = (
        "📅 **የህብረቱ መደበኛ ሳምንታዊ ፕሮግራሞች**\n"
        "• ⛪ **የአርብ ምሽት አምልኮና ትምህርት፦** ከምሽቱ 11:30 - 2:00 (በዋናው ግቢ ግቢ ጉባኤ)\n"
        "• ☀️ **የእሁድ ጠዋት ታላቅ አምልኮ፦** ከጠዋቱ 2:30 - 6:00\n"
        "• 🙏 **የእለት ተእለት የጸሎት ፕሮግራም፦** በየቀኑ ማለዳ 12:00 - 1:00\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💰 **አገልግሎታችንን ለመደገፍ (Financial Support)፦**\n\n"
        "🏦 **የኢትዮጵያ ንግድ ባንክ (CBE)፦**\n"
        "🟢🟢 **1000703058993** 🟢🟢\n"
        "👤 *(FEKADU AYELE AND MEETI WAYUMA)*\n\n"
        "“እግዚአብሔር በደስታ የሚሰጠውን ይወዳልና።” — 2ቆሮ 9:7"
    )
    await callback_query.message.edit_text(text=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")

# --- 5. Daily Bible Life (Boilerplate) ---
@dp.callback_query(lambda c: c.data == "menu_bible")
async def bible_handler(callback_query: CallbackQuery):
    bible_text = (
        "📖 **Daily Bible Life (የዕለት ተዕለት የቃል ሕይወት)**\n\n"
        "“ሰው ከእግዚአብሔር አፍ በሚወጣ ቃል ሁሉ እንጂ በእንጀራ ብቻ አይኖርም ተብሎ ተጽፎአል።” — ማቴ 4:4\n\n"
        "ይህ ክፍል ተማሪዎች በየቀኑ ያነበቡትን የመጽሐፍ ቅዱስ ክፍል ሪፖርት የሚያደርጉበትና መንፈሳዊ ጉዟቸውን የሚገመግሙበት ነው።\n\n"
        "⚙️ *የዕለቱ የንባብ ማመሳከሪያና የቼክ-ኢን (Check-in) ሲስተም በሚቀጥለው አፕዴት ይዘመናል!*"
    )
    await callback_query.message.edit_text(text=bible_text, reply_markup=get_back_keyboard())

# --- የአድሚን መቆጣጠሪያ ኮማንድ ---
@dp.message(Command("view_students"))
async def view_students_handler(message: Message):
    if message.chat.id != ADMIN_CHAT_ID:
        return 
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.full_name, s.phone, s.department, s.year, s.campus, 
               (SELECT group_concat(team_name, ' | ') FROM team_registrations WHERE chat_id = s.chat_id) as teams
        FROM students s
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("📝 እስካሁን በዳታቤዙ ውስጥ ምንም የተመዘገበ ተማሪ የለም።")
        return
        
    report = f"📋 **በዳታቤዝ ውስጥ ያሉ የተመዘገቡ ተማሪዎች ({len(rows)})፦**\n\n"
    for i, row in enumerate(rows, 1):
        teams_list = row[5] if row[5] else "ለአገልግሎት አልተመዘገበም"
        report += (f"{i}. 👤 **ስም፦** {row[0]}\n"
                   f"   📱 **ስልክ፦** {row[1]}\n"
                   f"   🏢 **ክፍል፦** {row[2]} ({row[3]}ኛ ዓመት) | 📍 {row[4]}\n"
                   f"   🔥 **የተመረጡ ቲሞች፦** {teams_list}\n\n")
    await message.answer(report, parse_mode="Markdown")

async def handle_render(request):
    return web.Response(text="DUEVASUE Fellowship Bot is Running Perfect with Full Team Data!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    init_db()
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
