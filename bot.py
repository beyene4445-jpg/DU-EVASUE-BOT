# --- 1. የቲም መቀላቀል ሃንድለር (ያለ ምዝገባ ቢመጡ እንኳን ይይዛቸዋል) ---
@dp.callback_query(F.data.startswith("join_"))
async def join_team(callback: CallbackQuery, state: FSMContext):
    team_code = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    
    # ተጠቃሚው ቀድሞ ተመዝግቧል ወይስ አላላ?
    conn = sqlite3.connect("duevasue.db")
    user = conn.execute("SELECT * FROM students WHERE chat_id=?", (chat_id,)).fetchone()
    conn.close()

    if not user:
        # ካልተመዘገበ፡ ቲሙን በ memory ይይዝና ምዝገባውን ያስጀምረዋል
        await state.update_data(chosen_team=team_code)
        await callback.message.edit_text("ቲሙን ለመቀላቀል በመጀመሪያ መመዝገብ አለብዎት።\n\n📝 እባክዎ **የመጀመሪያ እና የአባት ስምዎን** ያስገቡ፦")
        await state.set_state(Registration.name)
    else:
        # ቀድሞ ከተመዘገበ፡ በቀጥታ ቲሙን ይመዘግብለታል
        team_name = TEAMS_DATA[team_code]["name"]
        conn = sqlite3.connect("duevasue.db")
        conn.execute('UPDATE students SET team = ? WHERE chat_id = ?', (team_name, chat_id))
        conn.commit()
        conn.close()
        await callback.message.edit_text(f"✅ እንኳን ደስ አለዎት! በ**{team_name}** ተመዝግበዋል።", 
                                          reply_markup=get_back_kb())

# --- 2. የምዝገባ መጨረሻ (Campus ምርጫ) ---
@dp.callback_query(Registration.campus)
async def proc_campus(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    campus = callback.data.replace("c_", "")
    team_name = TEAMS_DATA.get(user_data.get("chosen_team"), {}).get("name", "ምንም") # ካለ ይይዛል
    
    # መረጃውን ወደ DB ማስገባት
    conn = sqlite3.connect("duevasue.db")
    cursor = conn.cursor()
    # ሙሉ ምዝገባ
    cursor.execute('INSERT OR REPLACE INTO students (chat_id, full_name, sex, phone, department, year, campus, team) VALUES (?,?,?,?,?,?,?,?)', 
                   (callback.message.chat.id, user_data['name'], user_data['sex'], user_data['phone'], 
                    user_data['dept'], user_data['year'], campus, team_name))
    conn.commit()
    conn.close()
    
    # የምዝገባ ማጠናቀቂያ መልእክት
    msg = "🎉 **ምዝገባዎ ተጠናቋል!**"
    if team_name != "ምንም":
        msg += f"\n\nእናም በ**{team_name}** ተመዝግበዋል።"
        
    await callback.message.edit_text(msg, reply_markup=get_main_menu())
    await state.clear()
