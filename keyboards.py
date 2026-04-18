from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from translations import COUNTRIES, LANGUAGES, CURRENCIES, get_text, VIDEO_CATEGORIES

def get_country_keyboard():
    buttons = []
    for code, country in COUNTRIES.items():
        buttons.append([KeyboardButton(text=country['name'])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_language_keyboard(country_code='KZ'):
    country = COUNTRIES.get(country_code.lower(), COUNTRIES['kz'])
    available_langs = country['languages']
    
    buttons = []
    for lang_code in available_langs:
        if lang_code in LANGUAGES:
            buttons.append([KeyboardButton(text=LANGUAGES[lang_code]['name'])])
    
    if 'en' not in available_langs:
        buttons.append([KeyboardButton(text=LANGUAGES['en']['name'])])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_currency_keyboard():
    buttons = []
    row = []
    for code, currency in list(CURRENCIES.items())[:4]:
        row.append(KeyboardButton(text=currency['name']))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    more = list(CURRENCIES.items())[4:]
    if more:
        buttons.append([KeyboardButton(text="💰 Другие валюты")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_all_currencies_keyboard():
    buttons = []
    for code, currency in CURRENCIES.items():
        buttons.append([KeyboardButton(text=currency['name'])])
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_main_keyboard(lang):
    buttons = [
        [KeyboardButton(text=get_text(lang, 'income')), KeyboardButton(text=get_text(lang, 'expense'))],
        [KeyboardButton(text=get_text(lang, 'goals')), KeyboardButton(text=get_text(lang, 'statistics'))],
        [KeyboardButton(text="👥 Shared Goals"), KeyboardButton(text=get_text(lang, 'videos'))],
        [KeyboardButton(text="💎 Премиум"), KeyboardButton(text=get_text(lang, 'settings'))],  # 👈 НОВАЯ КНОПКА
        [KeyboardButton(text=get_text(lang, 'help'))]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_keyboard(lang):
    buttons = [[KeyboardButton(text=get_text(lang, 'cancel'))]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_categories_keyboard(lang, trans_type='expense'):
    categories = ['food', 'transport', 'entertainment', 'salary', 'education', 'health', 'house', 'communication', 'other']
    buttons = []
    for cat in categories:
        cat_text = get_text(lang, 'categories').get(cat, cat)
        buttons.append([KeyboardButton(text=cat_text)])
    buttons.append([KeyboardButton(text=get_text(lang, 'cancel'))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_settings_keyboard(lang):
    buttons = [
        [KeyboardButton(text=get_text(lang, 'change_language'))],
        [KeyboardButton(text=get_text(lang, 'change_currency'))],
        [KeyboardButton(text=get_text(lang, 'delete_all_data'))],
        [KeyboardButton(text=get_text(lang, 'main_menu'))]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_delete_confirmation_keyboard(lang):
    buttons = [
        [KeyboardButton(text=get_text(lang, 'confirm_yes')), KeyboardButton(text=get_text(lang, 'confirm_no'))]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_goal_actions_keyboard(lang):
    add_money_texts = {
        'ru': '💰 Добавить деньги в цель',
        'en': '💰 Add money to goal',
        'kz': '💰 Мақсатқа ақша қосу',
        'ua': '💰 Додати гроші в ціль',
        'ky': '💰 Максатка акча кошуу'
    }
    add_money_text = add_money_texts.get(lang, '💰 Add money to goal')
    
    buttons = [
        [KeyboardButton(text=add_money_text)],  # Добавить деньги
        [KeyboardButton(text="➕ Создать новую цель")],  # НОВАЯ КНОПКА
        [KeyboardButton(text=get_text(lang, 'delete_goal'))],
        [KeyboardButton(text=get_text(lang, 'main_menu'))]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_video_categories_keyboard(lang):
    buttons = []
    categories = VIDEO_CATEGORIES.get(lang, VIDEO_CATEGORIES['en'])
    for cat_key, cat_name in categories.items():
        buttons.append([KeyboardButton(text=cat_name)])
    buttons.append([KeyboardButton(text=get_text(lang, 'main_menu'))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_shared_goals_keyboard():
    buttons = [
        [KeyboardButton(text="➕ Create Shared Goal")],
        [KeyboardButton(text="🔗 Join Shared Goal")],
        [KeyboardButton(text="📋 My Shared Goals")],
        [KeyboardButton(text="🏠 Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_shared_goal_actions_keyboard():
    buttons = [
        [KeyboardButton(text="💰 Add Money")],
        [KeyboardButton(text="📊 View Progress")],
        [KeyboardButton(text="◀️ Back")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)