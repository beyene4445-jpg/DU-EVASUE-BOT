import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
BOT_TOKEN = "8344884558:AAEUR_FkFjnAF5AHdCfptH3UWaZYumshlyU"
ADMIN_CHAT_ID = "6120164042"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- TEAMS DATA ---
TEAMS_DATA = {
    "Prayer": {"name": "🙏 የጸሎት ቡድን", "desc": "ይህ የጸሎት ቲም በፌሎሺፓችን ስለ ግል ህይወታችን፣ ስለ ሌሎች፣ ስለ ህብረታችን፣ ስለ ሀገራችን... ወዘተ የሚጸለይበት እንዲሁም የተለያዩ የጸሎት መርሃግብሮችን በማዘጋጀት ሌሎችን ለጸሎት የማስተባበርን አገልግሎት ያከናውናል።\n📅 የቲም ቀን ዘወትር ሰኞ ከ 11:00-1:30"},
    "Counseling": {"name": "🧠 የማማከር አገልግሎት", "desc": "ይህ ቲም ክርስቲያን ተማሪዎችን በመንፈሳዊ፣ በማህበራዊ፣ በሥነ-ልቦናዊ እና ትምህርታዊ ጉዳዮች ዙሪያ የምክክር አገልግሎት የፈጽማል፣ ይጸልያል፣ ይከታተላል።\n📅 የቲም ቀን ዘወትር ሰኞ 11:00-1:30."},
    "Teaching": {"name": "📖 ትምህርት እና ስልጠና", "desc": "ይህ ቲም ተማሪዎች በመንፈሳዊ ሕይወት እንዲያድጉ አስፈላጊዉን ትምህርት እና ስልጠና ያዘጋጃል፣ ይሰጣል። በሕብረቱ ውስጥ ያሉትን የመጽሐፍ ቅዱስ ቡድኖች ያደራጃል፣ በጥናት ወቅትም ይከታተላል።\n📅 የቲም ቀን ዘወትር ማክሰኞ 11:00-1:30."},
    "Evan": {"name": "🔥 EVAN Mobilizer", "desc": "ይህ ቲም ዋና ትኩረቱን የወንጌል ምስክርነት ላይ በማድረግ ግቢ ወስጥ ላሉ ላልዳኑ ነፍሳት ወንጌልን መመስከር፣ ሌሎችን ለወንጌል ምስክርነት ማነሳሳት፣ በየጊዜው ከግቢ ውጭ ባሉ አካባቢዎች የወንጌል ስርጭት ያከናውናል።\n📅 የቲም ቀን ማክሰኞ 11:00-1:30."},
    "Worship": {"name": "🎵 የአምልኮ ቡድን", "desc": "ሕብረቱ ባሉት የአምልኮ ፕሮግራሞች ላይ በመዝሙር የአምልኮ ፕሮግራሙን ይመራል። አዳዲስ መዝሙሮችን ይለቃል።\n📅 የቲም ቀን ማክሰኞ 11:00-1:30."},
    "Love": {"name": "🤝 ፍቅርና የርህራሄ አገልግሎት", "desc": "ይህ ህብረት በተለያዩ ጉዳዮች ቁሳዊ እንዲሁም ስነልቦናዊ ድጋፍ ለሚያስፈልጋቸው ተማሪዎች የድጋፍ አገልግሎትን ይሰጣል። በሆስፒታሎች እና ማረሚያ ቤቶች ይጎበኛል።\n📅 የቲም ቀን ዘውትር እሮብ 11:00-1:30."},
    "Art": {"name": "🎭 ድራማ እና ስነጽሁፍ", "desc": "ይህ ህብረት መንፈሳዊ እና መጽሐፍ ቅዱሳዊ ይዘት ያላቸው ድራማ እና ፊልም፣ ግጥም፣ ትረካ እና ምሳሌዎችን ያዘጋጃል፣ በተለያዩ ልዩ ፕሮግራሞች ላይ ያቀርባል።\n📅 የቲም ቀን ዘውትር እሮብ 11:00-1:30."},
    "Fund": {"name": "💰 FUNDRAISING", "desc": "ለሕብረቱ ገቢ ለማስገኘት ማንኛውንም አግባብ ያለው የፈጠራ ክህሎት በመጠቀም ለወንጌል ሥራ የሚሆን ገቢ ያሰባስባል።\n📅 የቲም ቀን ሰኞ 11፡00 - 1:30"},
    "Natanim": {"name": "🧹 መስተንግዶ /ናታኒም/", "desc": "ሰዎችን ማስተናገድ፣ መባ መሰብሰብ፣ ስጦታዎችን መቀበል፣ የፅዳት ተግባራትን ማከናወን እና የሕብረቱን ንብረት በኃላፊነት መጠበቅ።\n📅 የቲም ቀን ቅዳሜ 11:00-1:30."},
    "Choir": {"name": "🎤 የመዘምራን ቡድን", "desc": "አዳዲስ ዝማሬዎችን በማዘጋጀት ለሕብረቱ ፕሮግራም ያቀርባሉ። የጸሎት እና የልምምድ ጊዜ አላቸው።\n📅 የቲም ቀን ቅዳሜ 11:00-1:30."},
    "Media": {"name": "📱 የማህበራዊ ሚዲያ", "desc": "ስለ ፌሎሺፕ የተለያዩ ፕሮግራሞችን መስራት፣ ፎቶ እና ቪዲዮ በማንሳት ማስታወሻ መያዝ፣ ወንጌልን በማህበራዊ ሚዲያ ማድረስ።"}
}

# --- FOOTER TEXT ---
FOOTER_TEXT = "\n\n━━━━━━━━━━━━━━\n✨ *FELLOWSHIP ምንጊዜም ቤታችን ነው* ✨"

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
    team = State()

# --- MENU LAYOUT ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 ለመመዝገብ (Register)", callback_data="menu_register")],
        [InlineKeyboardButton(text="👤 የእኔ መረጃ", callback_data="menu_profile")],
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
    await message.answer(f"እንኳን ወደ DUEVASUE FELLOWSHIP BOT በደህና መጡ! {FOOTER_TEXT}", reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "go_home")
async def go_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"እንኳን ወደ DUEVASUE FELLOWSHIP BOT በደህና መጡ! {FOOTER_TEXT}", reply_markup=get_main_menu(), parse_mode="Markdown")

# --- PROFILE HANDLER ---
@dp.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    conn = sqlite3.connect("duevasue.db")
    user = conn.execute("SELECT * FROM students WHERE chat_id=?", (callback.message.chat.id,)).fetchone()
    conn.close()

    if user:
        gender_display = "ወንድ" if user[2] == "sex_m" else "ሴት"
        profile_text = (
            f"👤 **የእርስዎ መረጃ**\n\n"
            f"ስም: {user[1]}\n"
            f"ጾታ: {gender_display}\n"
            f"ስልክ: {user[3]}\n"
            f"ዲፓርትመንት: {user[4]}\n"
            f"ዓመት: {user[5]}\n"
            f"ካምፓስ: {user[6]}\n"
            f"ቲም: {user[7]}"
            f"{FOOTER_TEXT}"
        )
        await callback.message.edit_text(profile_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]), parse_mode="Markdown")
    else:
        await callback.message.edit_text(f"እርስዎ ገና አልተመዘገቡም።\n\nእባክዎ በመጀመሪያ ይመዝገቡ። {FOOTER_TEXT}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 ለመመዝገብ", callback_data="menu_register")], [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]), parse_mode="Markdown")

# --- BIBLE LIFE HANDLER ---
@dp.callback_query(F.data == "menu_bible")
async def show_bible(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 **Daily Bible Life**\n\nዛሬ መጽሐፍ ቅዱስ አንብበሃል?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ አዎ", callback_data="bible_yes"), InlineKeyboardButton(text="❌ አይ", callback_data="bible_no")],
            [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]
        ]), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("bible_"))
async def bible_response(callback: CallbackQuery):
    if callback.data == "bible_yes":
        msg = "አሜን! እግዚአብሔር ይባርክህ። ቃሉን ማሰላሰልህ ህይወትህ እንዲታደስ ያደርጋል።\n\n“እግዚአብሔርን ፈልጉት ትጸናላችሁም፤ ሁልጊዜ ፊቱን ፈልጉ።” — መዝሙር 105፥4"
    else:
        msg = "አይዞህ፣ አሁኑኑ ተነሳና ትንሽ ቃል አንብብ። የጌታ ቃል ለህይወትህ የሚያስፈልገውን ብርሃን ይሰጥሃል።\n\nየዛሬው ምክር፦ 'ጊዜ የለኝም አትበል፣ ለጌታ ቃል ጊዜ ስጠው።'"
    await callback.message.edit_text(f"{msg}{FOOTER_TEXT}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]), parse_mode="Markdown")

# --- ABOUT HANDLER ---
@dp.callback_query(F.data == "menu_about")
async def show_about(callback: CallbackQuery):
    about_text = (
        "ℹ️ **ስለ እኛ (About Us)**\n\n"
        "**ዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት (DUEVASUE)**\n\n"
        "✨ *ምንነታችን*\n"
        "እስከ ክርስቶስ ፍጹምነት ድረስ የምናድግ፣ የተጠራንበትን አገልግሎት በታማኝነት የምናገለግል፣ በህብረት የምንኖር የዲላ ዩኒቨርሲቲ ወንጌላውያን ክርስቲያን ተማሪዎች ህብረት ነን።\n\n"
        "🎯 *ተቀዳሚ ዓላማዎቻችን (Aims)*\n"
        "1. ተማሪዎችን በማገልገል የእግዚአብሔርን መንግስት ማጽናት (Evangelism)\n"
        "2. የህብረቱን አባላት በደቀመዝሙርነት ትምህርት ማዳበር (Discipleship)\n"
        "3. በክርስቶስ እምነት የጸኑ ተማሪዎችን በአገልግሎት በመጠቀም ክብሩን መግለጽ\n"
        "4. ተማሪዎች በትምህርታቸው ጥሩ ውጤት በማምጣት እግዚአብሔርን እንዲያስከብሩ ድጋፍ ማድረግ\n"
        "5. የቤተክርስቲያን እና የሀገር መሪዎችን ማፍራት (Leadership Development)\n\n"
        "💎 *እሴቶቻችን (Values)*\n"
        "1. በቃለ እግዚአብሔር መጽናት\n"
        "2. ትኩረታችን ተማሪዎች ናቸው\n"
        "3. የቤተ እምነት፣ የቋንቋ እና የኢኮኖሚ ልዩነትን መሻገር\n\n"
        "“እግዚአብሔርን ፈልጉት ትጸናላችሁም፤ ሁልጊዜ ፊቱን ፈልጉ።” — መዝሙር 105፥4\n\n"
        f"{FOOTER_TEXT}"
    )
    await callback.message.edit_text(about_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]]), parse_mode="Markdown", disable_web_page_preview=True)

# --- PROGRAM HANDLER ---
@dp.callback_query(F.data == "menu_program")
async def show_program(callback: CallbackQuery):
    prog_text = (
        "📅 **Program & Support**\n\n"
        "የህብረታችን ሳምንታዊ ዋና ፕሮግራም፦\n"
        "የአምልኮ እና የቃል ጊዜ፦ *ዘወትር ዓርብ ከ 11:00 - 2:00*\n\n"
        "ለድጋፍ እና ለልገሳ፦\n"
        "ባንክ፦ ንግድ ባንክ (CBE)\n"
        "አካውንት፦ 1000703058993 (Fikadu)\n\n"
        f"{FOOTER_TEXT}"
    )
    await callback.message.edit_text(prog_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")]
    ]), parse_mode="Markdown")

# --- TEAMS HANDLER ---
@dp.callback_query(F.data == "menu_teams")
async def show_teams(callback: CallbackQuery):
    kb = [[InlineKeyboardButton(text=data["name"], callback_data=f"view_{code}")] for code, data in TEAMS_DATA.items()]
    kb.append([InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="go_home")])
    await callback.message.edit_text(f"👥 **የአገልግሎት ዘርፎች**\nአንዱን ይምረጡ፦{FOOTER_TEXT}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("view_"))
async def view_team(callback: CallbackQuery):
    code = callback.data.split("_")[1]
    team = TEAMS_DATA[code]
    kb = [[InlineKeyboardButton(text="✅ ይህንን ቲም ተቀላቀል", callback_data=f"join_{code}")], [InlineKeyboardButton(text="⬅️ ተመለስ", callback_data="menu_teams")]]
    await callback.message.edit_text(f"🔹 **{team['name']}**\n\n{team['desc']}{FOOTER_TEXT}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# --- JOIN TEAM LOGIC ---
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
        await callback.message.edit_text(f"✅ እንኳን ደስ አለዎት! በ**{TEAMS_DATA[team_code]['name']}** ተመዝግበዋል።{FOOTER_TEXT}", reply_markup=get_main_menu(), parse_mode="Markdown")

# --- REGISTRATION ---
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
    await state.update_data(campus=callback.data.split("_")[1])
    kb = [[InlineKeyboardButton(text=data["name"], callback_data=f"sel_{code}")] for code, data in TEAMS_DATA.items()]
    await callback.message.edit_text("💡 ለመመዝገብ የመጨረሻው እርምጃ! እባክዎ የሚፈልጉትን የአገልግሎት ቡድን ይምረጡ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(Registration.team)

@dp.callback_query(Registration.team)
async def proc_team(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    team_code = callback.data.split("_")[1]
    team_name = TEAMS_DATA[team_code]["name"]
    
    gender_display = "ወንድ" if user_data['sex'] == "sex_m" else "ሴት"
    
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?)', 
                   (callback.message.chat.id, user_data['name'], user_data['sex'], user_data['phone'], user_data['dept'], user_data['year'], user_data['campus'], team_name))
    conn.commit()
    conn.close()

    admin_message = (
        f"🔔 **አዲስ የተመዘገበ ተማሪ**\n\n"
        f"👤 ስም: {user_data['name']}\n"
        f"⚧ ጾታ: {gender_display}\n"
        f"📱 ስልክ: {user_data['phone']}\n"
        f"🏢 ዲፓርትመንት: {user_data['dept']}\n"
        f"🎓 ዓመት: {user_data['year']}\n"
        f"📍 ካምፓስ: {user_data['campus']}\n"
        f"🛠 የተመደበበት ቲም: {team_name}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"አድሚን ጋር መልእክት ለመላክ አልተቻለም: {e}")
    
    await callback.message.edit_text(f"🎉 **ምዝገባው ተጠናቋል!**\n\nቲም፦ {team_name}{FOOTER_TEXT}", reply_markup=get_main_menu(), parse_mode="Markdown")
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
