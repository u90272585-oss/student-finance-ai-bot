import asyncio
import logging
import csv
import io
import random
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
from dotenv import load_dotenv

from database import Database
from translations import get_text, COUNTRIES, LANGUAGES, CURRENCIES, VIDEO_CATEGORIES
from keyboards import (
    get_country_keyboard, get_language_keyboard, get_currency_keyboard,
    get_all_currencies_keyboard, get_main_keyboard, get_cancel_keyboard,
    get_categories_keyboard, get_settings_keyboard, get_delete_confirmation_keyboard,
    get_goal_actions_keyboard, get_video_categories_keyboard,
    get_shared_goals_keyboard, get_shared_goal_actions_keyboard
)
from plant_goals import get_plant_text, get_plant_choice_keyboard, PLANT_TYPES

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

class SetupState(StatesGroup):
    country = State()
    language = State()
    currency = State()

class TransactionState(StatesGroup):
    amount = State()
    category = State()
    note = State()

class GoalState(StatesGroup):
    name = State()
    amount = State()
    plant_choice = State()
    select_for_delete = State()
    confirm_delete = State()
    select_for_add_money = State()
    enter_add_amount = State()

class SettingsState(StatesGroup):
    action = State()
    language = State()
    currency = State()
    delete_data = State()
    confirm_delete_all = State()

class VideoState(StatesGroup):
    category = State()

class SharedGoalState(StatesGroup):
    create_name = State()
    create_target = State()
    join_goal = State()
    add_money = State()
    select_for_add = State()
    enter_amount = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if user:
        lang = user[3]
        await message.answer(
            get_text(lang, 'main_menu'),
            reply_markup=get_main_keyboard(lang),
            parse_mode="HTML"
        )
        await send_daily_tip(message, lang)
    else:
        await message.answer(
            "🌟 <b>Welcome to Finance Bot - Your Personal Financial Assistant for CIS Countries!</b>\n\n"
            "💼 <i>Track your money, achieve goals, and build wealth!</i>\n\n"
            "✨ <b>What you can do:</b>\n"
            "💰 Track income and expenses\n"
            "🎯 Set and achieve financial goals\n"
            "📊 View detailed statistics\n"
            "💡 Get daily financial tips\n"
            "📺 Watch educational videos\n"
            "👥 Create shared goals with friends\n\n"
            "Let's get started! First, select your country:",
            reply_markup=get_country_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(SetupState.country)

async def send_daily_tip(message: types.Message, lang: str):
    tip = db.get_daily_tip()
    if tip:
        video = db.get_random_video(lang)
        if video:
            video_title, video_url, duration, description = video
            tip_text = get_text(lang, 'daily_tip_with_video').format(
                tip=tip['tip'],
                video_title=video_title,
                duration=duration,
                video_url=video_url,
                description=description[:100] + "..." if len(description) > 100 else description
            )
        else:
            tip_text = get_text(lang, 'daily_tip').format(tip=tip['tip'])
        
        await message.answer(tip_text, parse_mode="HTML", disable_web_page_preview=False)

@dp.message(Command("tip"))
async def cmd_tip(message: types.Message):
    user = db.get_user(message.from_user.id)
    if user:
        lang = user[3]
        tip = db.get_random_tip()
        if tip:
            video = db.get_random_video(lang)
            if video:
                video_title, video_url, duration, description = video
                tip_text = get_text(lang, 'daily_tip_with_video').format(
                    tip=tip['tip'],
                    video_title=video_title,
                    duration=duration,
                    video_url=video_url,
                    description=description[:100] + "..." if len(description) > 100 else description
                )
            else:
                tip_text = get_text(lang, 'daily_tip').format(tip=tip['tip'])
            
            await message.answer(tip_text, parse_mode="HTML", disable_web_page_preview=False)
        else:
            await message.answer(get_text(lang, 'no_tips'))

@dp.message(Command("video"))
async def cmd_random_video(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, None)
        return
    
    lang = user[3]
    video = db.get_random_video(lang)
    
    if video:
        video_title, video_url, duration, description = video
        text = get_text(lang, 'random_video').format(
            title=video_title,
            duration=duration,
            description=description,
            url=video_url
        )
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=False)
    else:
        await message.answer(get_text(lang, 'no_tips'))

@dp.message(lambda m: m.text in [get_text('ru', 'videos'), get_text('en', 'videos'), get_text('kz', 'videos'), get_text('ua', 'videos')])
async def show_videos(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    if lang not in ['ru', 'en']:
        lang = 'en'
    
    text = get_text(lang, 'videos_title')
    await message.answer(
        text,
        reply_markup=get_video_categories_keyboard(lang),
        parse_mode="HTML"
    )
    await state.set_state(VideoState.category)

@dp.message(VideoState.category)
async def show_videos_by_category(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    if lang not in ['ru', 'en']:
        lang = 'en'
    
    selected_category = None
    categories_dict = VIDEO_CATEGORIES.get(lang, VIDEO_CATEGORIES['en'])
    
    for cat_key, cat_name in categories_dict.items():
        if message.text == cat_name:
            selected_category = cat_key
            break
    
    if not selected_category:
        if message.text == get_text(lang, 'main_menu'):
            await state.clear()
            await back_to_main(message)
            return
        else:
            await message.answer(get_text(lang, 'select_category'))
            return
    
    videos = db.get_videos_by_category(lang, selected_category)
    
    if not videos:
        await message.answer("❌ No videos found in this category.")
        await state.clear()
        return
    
    category_name = categories_dict[selected_category]
    text = get_text(lang, 'videos_category').format(
        category=category_name,
        count=len(videos)
    )
    
    for video in videos:
        video_id, title, url, duration, description, level = video
        text += get_text(lang, 'video_item').format(
            title=title,
            duration=duration,
            description=description[:150] + "..." if len(description) > 150 else description,
            url=url
        )
    
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=False)
    await message.answer(
        get_text(lang, 'main_menu'),
        reply_markup=get_main_keyboard(lang)
    )
    await state.clear()

@dp.message(SetupState.country)
async def setup_country(message: types.Message, state: FSMContext):
    country_name = message.text
    country_code = None
    for code, country in COUNTRIES.items():
        if country['name'] == country_name:
            country_code = code
            break
    
    if not country_code:
        await message.answer("❌ Please select a country from the list!")
        return
    
    await state.update_data(country=country_code)
    await message.answer(
        "🌐 Now select your language:",
        reply_markup=get_language_keyboard(country_code)
    )
    await state.set_state(SetupState.language)

@dp.message(SetupState.language)
async def setup_language(message: types.Message, state: FSMContext):
    lang_name = message.text
    lang_code = None
    for code, lang in LANGUAGES.items():
        if lang['name'] == lang_name:
            lang_code = code
            break
    
    if not lang_code:
        await message.answer("❌ Please select a language from the list!")
        return
    
    await state.update_data(language=lang_code)
    
    if lang_code == 'ru':
        await message.answer(
            "💰 Теперь выберите валюту:",
            reply_markup=get_currency_keyboard()
        )
    elif lang_code == 'kz':
        await message.answer(
            "💰 Енді валютаны таңдаңыз:",
            reply_markup=get_currency_keyboard()
        )
    elif lang_code == 'ua':
        await message.answer(
            "💰 Тепер виберіть валюту:",
            reply_markup=get_currency_keyboard()
        )
    else:
        await message.answer(
            "💰 Now select your currency:",
            reply_markup=get_currency_keyboard()
        )
    await state.set_state(SetupState.currency)

@dp.message(SetupState.currency)
async def setup_currency(message: types.Message, state: FSMContext):
    currency_name = message.text
    
    if currency_name in ["💰 Другие валюты", "💰 Other currencies"]:
        await message.answer(
            "💰 Select currency from the list:",
            reply_markup=get_all_currencies_keyboard()
        )
        return
    
    currency_code = None
    for code, currency in CURRENCIES.items():
        if currency['name'] == currency_name:
            currency_code = code
            break
    
    if not currency_code:
        await message.answer("❌ Please select a currency from the list!")
        return
    
    data = await state.get_data()
    user_id = message.from_user.id
    selected_lang = data['language']
    
    db.add_user(
        user_id,
        message.from_user.first_name,
        data['country'],
        selected_lang,
        currency_code
    )
    
    await message.answer(
        get_text(selected_lang, 'setup_complete').format(
            country=COUNTRIES[data['country']]['name'],
            language=LANGUAGES[selected_lang]['name'],
            currency=CURRENCIES[currency_code]['symbol']
        ),
        parse_mode="HTML"
    )
    
    await message.answer(
        get_text(selected_lang, 'main_menu'),
        reply_markup=get_main_keyboard(selected_lang),
        parse_mode="HTML"
    )
    await state.clear()

@dp.message(lambda m: m.text in [get_text('ru', 'income'), get_text('kz', 'income'), get_text('en', 'income'), get_text('ua', 'income'),
                                   get_text('ru', 'expense'), get_text('kz', 'expense'), get_text('en', 'expense'), get_text('ua', 'expense')])
async def handle_transaction(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    text = message.text
    trans_type = 'income' if text in [get_text('ru', 'income'), get_text('kz', 'income'), get_text('en', 'income'), get_text('ua', 'income')] else 'expense'
    
    await state.update_data(type=trans_type)
    await message.answer(
        get_text(lang, 'enter_amount'),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(TransactionState.amount)

@dp.message(TransactionState.amount)
async def transaction_amount(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        await message.answer(
            get_text(lang, 'select_category'),
            reply_markup=get_categories_keyboard(lang)
        )
        await state.set_state(TransactionState.category)
    except:
        await message.answer(get_text(lang, 'invalid_number'))

@dp.message(TransactionState.category)
async def transaction_category(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    await state.update_data(category=message.text)
    await message.answer(
        get_text(lang, 'enter_description'),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(TransactionState.note)

@dp.message(TransactionState.note)
async def transaction_note(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    data = await state.get_data()
    note = "" if message.text == "/skip" else message.text
    
    db.add_transaction(message.from_user.id, data['type'], data['amount'], data['category'], note)
    
    if data['type'] == 'income':
        db.update_goal_progress(message.from_user.id, data['amount'])
    
    await message.answer(
        get_text(lang, 'transaction_saved').format(
            type=get_text(lang, 'income_text') if data['type'] == 'income' else get_text(lang, 'expense_text'),
            amount=data['amount'],
            currency=CURRENCIES[currency]['symbol'],
            category=data['category'],
            description=f"\nDescription: {note}" if note else ""
        ),
        reply_markup=get_main_keyboard(lang)
    )
    await state.clear()

@dp.message(lambda m: m.text in [get_text('ru', 'statistics'), get_text('kz', 'statistics'), get_text('en', 'statistics'), get_text('ua', 'statistics')])
async def show_statistics(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, None)
        return
    
    lang = user[3]
    currency = user[4]
    income, expense, balance, top_cats = db.get_stats(message.from_user.id)
    
    text = get_text(lang, 'stats_title').format(days=30) + "\n\n"
    text += get_text(lang, 'stats_income').format(amount=income, currency=CURRENCIES[currency]['symbol']) + "\n"
    text += get_text(lang, 'stats_expense').format(amount=expense, currency=CURRENCIES[currency]['symbol']) + "\n"
    text += "━━━━━━━━━━━━━━━━\n"
    text += get_text(lang, 'stats_balance').format(amount=balance, currency=CURRENCIES[currency]['symbol']) + "\n\n"
    
    if top_cats:
        text += get_text(lang, 'stats_top') + "\n"
        for cat, amount in top_cats:
            percent = (amount / expense * 100) if expense > 0 else 0
            text += f"• {cat}: {amount:,.0f} {CURRENCIES[currency]['symbol']} ({percent:.0f}%)\n"
    
    text += f"\n{get_text(lang, 'stats_good') if balance > 0 else get_text(lang, 'stats_bad')}"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard(lang))

@dp.message(lambda m: m.text in [get_text('ru', 'goals'), get_text('kz', 'goals'), get_text('en', 'goals'), get_text('ua', 'goals')])
async def show_goals(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, None)
        return
    
    lang = user[3]
    currency = user[4]
    goals = db.get_goals(message.from_user.id)
    
    if not goals:
        await message.answer(get_text(lang, 'no_goals'), reply_markup=get_main_keyboard(lang))
        return
    
    text = get_text(lang, 'your_goals') + "\n\n"
    
    for goal_id, name, target, current in goals:
        percent = (current / target * 100) if target > 0 else 0
        
        plant_type = db.get_goal_plant(goal_id)
        plant_display = get_plant_text(plant_type, percent, current, target, CURRENCIES[currency]['symbol'], lang)
        
        text += plant_display + "\n" + "─" * 30 + "\n"
    
    text += "\n" + get_text(lang, 'goal_actions')
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_goal_actions_keyboard(lang))

@dp.message(lambda m: m.text in [get_text('ru', 'delete_goal'), get_text('kz', 'delete_goal'), get_text('en', 'delete_goal'), get_text('ua', 'delete_goal')])
async def delete_goal_select(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    goals = db.get_goals(message.from_user.id)
    
    if not goals:
        await message.answer(get_text(lang, 'no_goals'), reply_markup=get_main_keyboard(lang))
        return
    
    text = get_text(lang, 'select_goal_to_delete') + "\n\n"
    keyboard_buttons = []
    
    for i, (goal_id, name, target, current) in enumerate(goals, 1):
        text += f"{i}. {name} ({current}/{target})\n"
        keyboard_buttons.append([KeyboardButton(text=f"{i}. {name}")])
    
    keyboard_buttons.append([KeyboardButton(text=get_text(lang, 'cancel'))])
    
    await state.update_data(goals=goals)
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True))
    await state.set_state(GoalState.select_for_delete)

@dp.message(GoalState.select_for_delete)
async def delete_goal_confirm(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    data = await state.get_data()
    goals = data.get('goals', [])
    
    selected_goal = None
    for goal in goals:
        if message.text == f"{goal[0]}. {goal[1]}" or message.text == goal[1]:
            selected_goal = goal
            break
    
    if not selected_goal:
        await message.answer(get_text(lang, 'invalid_selection'))
        return
    
    await state.update_data(goal_to_delete=selected_goal)
    await message.answer(
        get_text(lang, 'confirm_delete_goal').format(name=selected_goal[1]),
        reply_markup=get_delete_confirmation_keyboard(lang)
    )
    await state.set_state(GoalState.confirm_delete)

@dp.message(GoalState.confirm_delete)
async def delete_goal_execute(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'confirm_yes'):
        data = await state.get_data()
        goal = data.get('goal_to_delete')
        
        if goal:
            db.delete_goal(goal[0])
            await message.answer(
                get_text(lang, 'goal_deleted').format(name=goal[1]),
                reply_markup=get_main_keyboard(lang)
            )
    elif message.text == get_text(lang, 'confirm_no'):
        await message.answer(get_text(lang, 'deletion_cancelled'), reply_markup=get_main_keyboard(lang))
    else:
        await message.answer(get_text(lang, 'invalid_choice'))
        return
    
    await state.clear()

@dp.message(Command("new_goal"))
async def new_goal_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    await message.answer(
        get_text(lang, 'enter_goal_name'),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(GoalState.name)

@dp.message(GoalState.name)
async def new_goal_name(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        get_text(lang, 'enter_goal_amount'),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(GoalState.amount)

@dp.message(GoalState.amount)
async def new_goal_amount(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        goal_id = db.add_goal(message.from_user.id, data['name'], amount)
        
        await state.update_data(goal_id=goal_id, goal_amount=amount, goal_name=data['name'])
        
        await message.answer(
            "🌸 Choose a flower for your goal!\n\n"
            "🌱 Each time you add money, your flower will grow!\n\n"
            "Select one:",
            reply_markup=get_plant_choice_keyboard(lang)
        )
        await state.set_state(GoalState.plant_choice)
        
    except:
        await message.answer(get_text(lang, 'invalid_number'))

@dp.message(GoalState.plant_choice)
async def goal_plant_choice(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=get_main_keyboard(lang))
        return
    
    selected_plant = None
    for plant_key, plant_data in PLANT_TYPES.items():
        if message.text == plant_data[f'name_{lang}']:
            selected_plant = plant_key
            break
    
    if not selected_plant:
        await message.answer("❌ Please select a flower from the list!")
        return
    
    data = await state.get_data()
    goal_id = data['goal_id']
    goal_name = data['goal_name']
    amount = data['goal_amount']
    
    db.set_goal_plant(goal_id, selected_plant)
    
    plant_text = get_plant_text(selected_plant, 0, 0, amount, CURRENCIES[currency]['symbol'], lang)
    
    await message.answer(
        get_text(lang, 'goal_created').format(
            name=goal_name,
            amount=amount,
            currency=CURRENCIES[currency]['symbol']
        ) + "\n\n" + plant_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(lang)
    )
    await state.clear()

@dp.message(Command("export_csv"))
async def export_csv(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, None)
        return
    
    lang = user[3]
    transactions = db.get_all_transactions(message.from_user.id)
    
    if not transactions:
        await message.answer(get_text(lang, 'no_transactions'))
        return
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Type', 'Amount', 'Category', 'Note', 'Date'])
    
    for trans in transactions:
        writer.writerow([trans[0], trans[1], trans[2], trans[3], trans[4], trans[5]])
    
    output.seek(0)
    file = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    await message.answer_document(
        types.BufferedInputFile(file.getvalue(), filename=f"finance_export_{datetime.now().strftime('%Y%m%d')}.csv"),
        caption=get_text(lang, 'export_success')
    )
    
    output.close()

@dp.message(lambda m: m.text in [get_text('ru', 'settings'), get_text('kz', 'settings'), get_text('en', 'settings'), get_text('ua', 'settings')])
async def show_settings(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    await message.answer(
        get_text(lang, 'settings_title'),
        reply_markup=get_settings_keyboard(lang),
        parse_mode="HTML"
    )

@dp.message(lambda m: m.text in [get_text('ru', 'delete_all_data'), get_text('kz', 'delete_all_data'), get_text('en', 'delete_all_data'), get_text('ua', 'delete_all_data')])
async def delete_all_data_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    await message.answer(
        get_text(lang, 'confirm_delete_all'),
        reply_markup=get_delete_confirmation_keyboard(lang),
        parse_mode="HTML"
    )
    await state.set_state(SettingsState.confirm_delete_all)

@dp.message(SettingsState.confirm_delete_all)
async def delete_all_data_execute(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'confirm_yes'):
        db.delete_all_user_data(message.from_user.id)
        await message.answer(
            get_text(lang, 'all_data_deleted'),
            reply_markup=get_main_keyboard(lang)
        )
    elif message.text == get_text(lang, 'confirm_no'):
        await message.answer(get_text(lang, 'deletion_cancelled'), reply_markup=get_main_keyboard(lang))
    else:
        await message.answer(get_text(lang, 'invalid_choice'))
        return
    
    await state.clear()

@dp.message(lambda m: m.text in [get_text('ru', 'change_language'), get_text('kz', 'change_language'), get_text('en', 'change_language'), get_text('ua', 'change_language')])
async def change_language_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    await message.answer(
        get_text(lang, 'select_language'),
        reply_markup=get_language_keyboard(user[2])
    )
    await state.set_state(SettingsState.language)

@dp.message(SettingsState.language)
async def change_language_set(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang_name = message.text
    
    lang_code = None
    for code, lang in LANGUAGES.items():
        if lang['name'] == lang_name:
            lang_code = code
            break
    
    if not lang_code:
        await message.answer("❌ Please select a language from the list!")
        return
    
    db.update_language(message.from_user.id, lang_code)
    
    await message.answer(
        get_text(lang_code, 'language_changed').format(language=lang_name),
        reply_markup=get_main_keyboard(lang_code)
    )
    await state.clear()

@dp.message(lambda m: m.text in [get_text('ru', 'change_currency'), get_text('kz', 'change_currency'), get_text('en', 'change_currency'), get_text('ua', 'change_currency')])
async def change_currency_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    await message.answer(
        get_text(lang, 'select_currency'),
        reply_markup=get_currency_keyboard()
    )
    await state.set_state(SettingsState.currency)

@dp.message(SettingsState.currency)
async def change_currency_set(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency_name = message.text
    
    if currency_name in ["💰 Другие валюты", "💰 Other currencies"]:
        await message.answer(
            "💰 Select currency from the list:",
            reply_markup=get_all_currencies_keyboard()
        )
        return
    
    currency_code = None
    for code, currency in CURRENCIES.items():
        if currency['name'] == currency_name:
            currency_code = code
            break
    
    if not currency_code:
        await message.answer("❌ Please select a currency from the list!")
        return
    
    db.update_currency(message.from_user.id, currency_code)
    await message.answer(
        get_text(lang, 'currency_changed').format(currency=currency_name),
        reply_markup=get_main_keyboard(lang)
    )
    await state.clear()

# ========== ОБЩИЕ ЦЕЛИ (SHARED GOALS) ==========

@dp.message(lambda m: m.text in ["👥 Shared Goals", "👥 Общие цели"])
async def shared_goals_menu(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    await message.answer(
        "👥 Shared Goals - Save together with friends!\n\nSelect an option:",
        reply_markup=get_shared_goals_keyboard()
    )

@dp.message(lambda m: m.text in ["➕ Create Shared Goal", "➕ Создать общую цель"])
async def create_shared_goal_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    await message.answer("🎯 Enter the name of your shared goal (e.g., 'Trip to Bali'):", reply_markup=get_cancel_keyboard(lang))
    await state.set_state(SharedGoalState.create_name)

@dp.message(SharedGoalState.create_name)
async def create_shared_goal_name(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await back_to_main(message)
        return
    
    await state.update_data(name=message.text)
    await message.answer("💰 Enter the target amount for your shared goal:", reply_markup=get_cancel_keyboard(lang))
    await state.set_state(SharedGoalState.create_target)

@dp.message(SharedGoalState.create_target)
async def create_shared_goal_target(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await back_to_main(message)
        return
    
    try:
        target = float(message.text.replace(',', '.'))
        data = await state.get_data()
        
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        goal_id = db.create_shared_goal(message.from_user.id, data['name'], target, invite_code)
        
        await message.answer(
            f"✅ Shared goal \"{data['name']}\" created!\n\n"
            f"Target: {target} {CURRENCIES[currency]['symbol']}\n\n"
            f"🔑 <b>Invite code:</b> <code>{invite_code}</code>\n\n"
            f"Share this code with your friends so they can join and contribute!",
            parse_mode="HTML",
            reply_markup=get_shared_goals_keyboard()
        )
        await state.clear()
    except:
        await message.answer("❌ Please enter a valid number!")

@dp.message(lambda m: m.text in ["🔗 Join Shared Goal", "🔗 Присоединиться"])
async def join_shared_goal_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    await message.answer("🔑 Enter the invite code shared by your friend:", reply_markup=get_cancel_keyboard(lang))
    await state.set_state(SharedGoalState.join_goal)

@dp.message(SharedGoalState.join_goal)
async def join_shared_goal_execute(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await back_to_main(message)
        return
    
    invite_code = message.text.strip().upper()
    result = db.join_shared_goal(message.from_user.id, invite_code)
    
    if result is None:
        await message.answer("❌ Invalid invite code. Please check and try again.", reply_markup=get_shared_goals_keyboard())
    elif result == 'already_member':
        await message.answer("⚠️ You are already a member of this goal!", reply_markup=get_shared_goals_keyboard())
    else:
        await message.answer(
            f"✅ You joined shared goal \"{result['name']}\"!\n\n"
            f"Target: {result['target']} {CURRENCIES[currency]['symbol']}\n"
            f"Current: {result['current']} {CURRENCIES[currency]['symbol']}\n\n"
            f"Start contributing to achieve it together!",
            reply_markup=get_shared_goals_keyboard()
        )
    await state.clear()

@dp.message(lambda m: m.text in ["📋 My Shared Goals", "📋 Мои общие цели"])
async def list_shared_goals(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    goals = db.get_user_shared_goals(message.from_user.id)
    
    if not goals:
        await message.answer("👥 You have no shared goals yet. Create one or join with an invite code!", reply_markup=get_shared_goals_keyboard())
        return
    
    text = "👥 <b>Your Shared Goals</b>\n\n"
    goals_list = []
    
    for goal in goals:
        goal_id, name, target, current, invite_code, creator_id, total_contributed = goal
        percent = (current / target * 100) if target > 0 else 0
        
        details = db.get_shared_goal_details(goal_id)
        members_count = len(details['members']) if details else 0
        
        text += f"🎯 <b>{name}</b>\n"
        text += f"💰 {current:.0f} / {target:.0f} {CURRENCIES[currency]['symbol']}\n"
        text += f"📊 Progress: {percent:.1f}%\n"
        text += f"🔑 Code: <code>{invite_code}</code>\n"
        text += f"👥 Members: {members_count}\n\n"
        goals_list.append(goal_id)
    
    await state.update_data(shared_goals_list=goals_list)
    await message.answer(text, parse_mode="HTML")
    await message.answer("Select a goal:", reply_markup=get_shared_goal_actions_keyboard())
    await state.set_state(SharedGoalState.select_for_add)

@dp.message(SharedGoalState.select_for_add)
async def select_shared_goal_action(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    
    if message.text in ["💰 Add Money", "💰 Добавить деньги"]:
        await message.answer("Enter the goal name or invite code to add money:")
        await state.set_state(SharedGoalState.add_money)
    elif message.text in ["📊 View Progress", "📊 Прогресс"]:
        await message.answer("Enter the goal name or invite code to view progress:")
        await state.set_state(SharedGoalState.enter_amount)
    elif message.text in ["◀️ Back", "◀️ Назад"]:
        await shared_goals_menu(message, state)
    else:
        await message.answer("Please choose an option from the menu!")

@dp.message(SharedGoalState.add_money)
async def add_money_to_shared_goal(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    goals = db.get_user_shared_goals(message.from_user.id)
    selected_goal = None
    
    for goal in goals:
        goal_id, name, target, current, invite_code, creator_id, total_contributed = goal
        if message.text.lower() == name.lower() or message.text.upper() == invite_code:
            selected_goal = goal
            break
    
    if not selected_goal:
        await message.answer("❌ Goal not found. Please check the name or invite code.")
        return
    
    await state.update_data(selected_goal=selected_goal)
    await message.answer(
        f"💰 Enter amount to add to \"{selected_goal[1]}\":",
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(SharedGoalState.enter_amount)

@dp.message(SharedGoalState.enter_amount)
async def process_shared_goal_amount(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await shared_goals_menu(message, state)
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        selected_goal = data.get('selected_goal')
        
        if not selected_goal:
            await shared_goals_menu(message, state)
            return
        
        goal_id, name, target, current, invite_code, creator_id, total_contributed = selected_goal
        
        completed = db.add_to_shared_goal(message.from_user.id, goal_id, amount)
        new_current = current + amount
        
        if completed:
            await message.answer(
                f"🎉🎉🎉 <b>CONGRATULATIONS!</b> 🎉🎉🎉\n\n"
                f"You and your friends reached the goal \"{name}\"!\n\n"
                f"Total saved: {new_current} {CURRENCIES[currency]['symbol']}\n\n"
                f"Well done! 🎊",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"✅ {amount} {CURRENCIES[currency]['symbol']} added to \"{name}\"!\n\n"
                f"New total: {new_current} / {target} {CURRENCIES[currency]['symbol']}\n\n"
                f"Keep going! 🎉"
            )
        
        details = db.get_shared_goal_details(goal_id)
        if details:
            goal = details['goal']
            members = details['members']
            percent = (goal[3] / goal[2] * 100) if goal[2] > 0 else 0
            
            contributors_text = ""
            for m in members:
                contributors_text += f"   • {m[1]}: {m[2]} {CURRENCIES[currency]['symbol']}\n"
            
            progress_text = (
                f"📊 <b>Shared Goal: {goal[1]}</b>\n\n"
                f"💰 Total: {goal[3]:.0f} / {goal[2]:.0f} {CURRENCIES[currency]['symbol']}\n"
                f"📈 Progress: {percent:.1f}%\n\n"
                f"👥 <b>Contributors:</b>\n{contributors_text}\n"
                f"🔑 Invite code: <code>{goal[4]}</code>"
            )
            await message.answer(progress_text, parse_mode="HTML")
        
        await state.clear()
        await shared_goals_menu(message, state)
        
    except:
        await message.answer("❌ Please enter a valid number!")

@dp.message(lambda m: m.text in [get_text('ru', 'help'), get_text('kz', 'help'), get_text('en', 'help'), get_text('ua', 'help')])
async def show_help(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, None)
        return
    
    lang = user[3]
    await message.answer(
        get_text(lang, 'help_text'),
        parse_mode="HTML",
        reply_markup=get_main_keyboard(lang)
    )

@dp.message(lambda m: m.text in [get_text('ru', 'main_menu'), get_text('kz', 'main_menu'), get_text('en', 'main_menu'), get_text('ua', 'main_menu')])
async def back_to_main(message: types.Message):
    user = db.get_user(message.from_user.id)
    if user:
        lang = user[3]
        await message.answer(
            get_text(lang, 'main_menu'),
            reply_markup=get_main_keyboard(lang),
            parse_mode="HTML"
        )

@dp.message()
async def handle_unknown(message: types.Message):
    user = db.get_user(message.from_user.id)
    if user:
        lang = user[3]
        await message.answer(
            get_text(lang, 'error'),
            reply_markup=get_main_keyboard(lang)
        )
    else:
        await cmd_start(message, None)

# ========== ДОБАВЛЕНИЕ ДЕНЕГ В ЛИЧНУЮ ЦЕЛЬ (ПРОСТОЙ И НАДЁЖНЫЙ ОБРАБОТЧИК) ==========

@dp.message(lambda m: m.text and m.text in ["💰 Add money to goal", "💰 Добавить деньги в цель", "💰 Мақсатқа ақша қосу", "💰 Додати гроші в ціль", "💰 Максатка акча кошуу"])
async def add_money_to_goal_select(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user[3]
    currency = user[4]
    
    goals = db.get_goals(message.from_user.id)
    
    if not goals:
        await message.answer("❌ You have no goals yet! Create one first.", reply_markup=get_main_keyboard(lang))
        return
    
    text = "🎯 Select a goal to add money:\n\n"
    keyboard_buttons = []
    
    for i, (goal_id, name, target, current) in enumerate(goals, 1):
        percent = (current / target * 100) if target > 0 else 0
        text += f"{i}. {name} ({current:.0f}/{target:.0f} {CURRENCIES[currency]['symbol']}) - {percent:.0f}%\n"
        keyboard_buttons.append([KeyboardButton(text=f"{i}. {name}")])
    
    keyboard_buttons.append([KeyboardButton(text=get_text(lang, 'cancel'))])
    
    await state.update_data(goals=goals)
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True))
    await state.set_state(GoalState.select_for_add_money)

@dp.message(GoalState.select_for_add_money)
async def add_money_to_goal_amount(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await back_to_main(message)
        return
    
    data = await state.get_data()
    goals = data.get('goals', [])
    
    selected_goal = None
    for goal in goals:
        if message.text == f"{goal[0]}. {goal[1]}" or message.text == goal[1]:
            selected_goal = goal
            break
    
    if not selected_goal:
        await message.answer("❌ Goal not found. Please select from the list!")
        return
    
    await state.update_data(selected_goal=selected_goal)
    await message.answer(
        f"💰 Enter amount to add to \"{selected_goal[1]}\":\n\n"
        f"Current: {selected_goal[3]:.0f} / {selected_goal[2]:.0f} {CURRENCIES[currency]['symbol']}",
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(GoalState.enter_add_amount)

@dp.message(GoalState.enter_add_amount)
async def add_money_to_goal_execute(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    lang = user[3]
    currency = user[4]
    
    if message.text == get_text(lang, 'cancel'):
        await state.clear()
        await back_to_main(message)
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        selected_goal = data.get('selected_goal')
        
        if not selected_goal:
            await back_to_main(message)
            return
        
        goal_id, name, target, current = selected_goal
        
        new_current = min(current + amount, target)
        db.cursor.execute('UPDATE goals SET current = ? WHERE id = ?', (new_current, goal_id))
        db.conn.commit()
        
        percent = (new_current / target * 100) if target > 0 else 0
        plant_type = db.get_goal_plant(goal_id)
        
        plant_display = get_plant_text(plant_type, percent, new_current, target, CURRENCIES[currency]['symbol'], lang)
        
        if new_current >= target:
            await message.answer(
                f"🎉🎉🎉 <b>GOAL COMPLETED!</b> 🎉🎉🎉\n\n"
                f"You reached your goal \"{name}\"!\n\n"
                f"{plant_display}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(lang)
            )
        else:
            await message.answer(
                f"✅ {amount:.0f} {CURRENCIES[currency]['symbol']} added to \"{name}\"!\n\n"
                f"{plant_display}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(lang)
            )
        
        await state.clear()
        
    except:
        await message.answer(get_text(lang, 'invalid_number'))

async def main():
    print("=" * 50)
    print("🚀 FINANCE BOT STARTED!")
    print("=" * 50)
    print("✅ Languages: Русский, Қазақша, English, Українська")
    print("✅ Currencies: KZT, RUB, UAH, USD, EUR, BYN, UZS, KGS")
    print("✅ Countries: USA, Kazakhstan, Russia, Ukraine, Belarus, Uzbekistan, Kyrgyzstan")
    print("✅ Features: Shared Goals, Videos, Tips, Export, Goal Flowers 🌸")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())