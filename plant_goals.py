# plant_goals.py - Растения для визуализации целей

PLANT_TYPES = {
    'lotus': {
        'name_ru': '🪷 Лотос',
        'name_en': '🪷 Lotus',
        'name_kz': '🪷 Лотос',
        'name_ua': '🪷 Лотос',
        'name_ky': '🪷 Лотос',
        'emoji': '🪷'
    },
    'rose': {
        'name_ru': '🌹 Роза',
        'name_en': '🌹 Rose',
        'name_kz': '🌹 Раушан',
        'name_ua': '🌹 Троянда',
        'name_ky': '🌹 Роза',
        'emoji': '🌹'
    },
    'sunflower': {
        'name_ru': '🌻 Подсолнух',
        'name_en': '🌻 Sunflower',
        'name_kz': '🌻 Күнбағыс',
        'name_ua': '🌻 Соняшник',
        'name_ky': '🌻 Күнкара',
        'emoji': '🌻'
    },
    'bamboo': {
        'name_ru': '🎋 Бамбук',
        'name_en': '🎋 Bamboo',
        'name_kz': '🎋 Баобаб',
        'name_ua': '🎋 Бамбук',
        'name_ky': '🎋 Бамбук',
        'emoji': '🎋'
    },
    'hibiscus': {
        'name_ru': '🌺 Гибискус',
        'name_en': '🌺 Hibiscus',
        'name_kz': '🌺 Гибискус',
        'name_ua': '🌺 Гібіскус',
        'name_ky': '🌺 Гибискус',
        'emoji': '🌺'
    }
}

def get_flower_art(plant_type, progress_percent):
    if plant_type == 'lotus':
        if progress_percent < 20:
            return "🪱"
        elif progress_percent < 40:
            return "🌱🪷"
        elif progress_percent < 60:
            return "🍃🪷🪷"
        elif progress_percent < 80:
            return "🌸🪷🪷🪷"
        elif progress_percent < 100:
            return "🪷🪷🪷🪷🌼"
        else:
            return "🌸🪷🌸🪷🌸"
    elif plant_type == 'rose':
        if progress_percent < 20:
            return "🌱"
        elif progress_percent < 40:
            return "🌿"
        elif progress_percent < 60:
            return "🌿🌹"
        elif progress_percent < 80:
            return "🌹🌹"
        elif progress_percent < 100:
            return "🌹🌹🌹"
        else:
            return "🌹🌹🌹🌹🌹"
    elif plant_type == 'sunflower':
        if progress_percent < 20:
            return "🌱"
        elif progress_percent < 40:
            return "🌿"
        elif progress_percent < 60:
            return "🌻"
        elif progress_percent < 80:
            return "🌻🌻"
        elif progress_percent < 100:
            return "🌻🌻🌻"
        else:
            return "🌻🌻🌻🌻🌻"
    elif plant_type == 'bamboo':
        if progress_percent < 20:
            return "🎍"
        elif progress_percent < 40:
            return "🎋"
        elif progress_percent < 60:
            return "🎋🎋"
        elif progress_percent < 80:
            return "🎋🎋🎋"
        elif progress_percent < 100:
            return "🎋🎋🎋🎋"
        else:
            return "🎋🎋🎋🎋🎋"
    else:
        if progress_percent < 20:
            return "🌱"
        elif progress_percent < 40:
            return "🌿"
        elif progress_percent < 60:
            return "🌺"
        elif progress_percent < 80:
            return "🌺🌺"
        elif progress_percent < 100:
            return "🌺🌺🌺"
        else:
            return "🌺🌺🌺🌺🌺"


def get_plant_text(plant_type, progress_percent, current, target, currency_symbol, lang='en'):
    flower_art = get_flower_art(plant_type, progress_percent)
    
    # Проверяем, есть ли такой язык в PLANT_TYPES, если нет - используем английский
    if f'name_{lang}' not in PLANT_TYPES[plant_type]:
        lang = 'en'
    
    plant_name = PLANT_TYPES[plant_type][f'name_{lang}']
    
    filled = int(progress_percent / 5)
    empty = 20 - filled
    progress_bar = "🌱" * min(filled, 3) + "░" * empty
    
    if progress_percent < 20:
        stage_texts = {
            'en': "🌱 Just planted! Keep watering with money!",
            'ru': "🌱 Только посажено! Поливай деньгами!",
            'kz': "🌱 Енді отырғызылды! Ақшамен суарыңыз!",
            'ua': "🌱 Тільки посаджено! Поливай грошима!",
            'ky': "🌱 Жаңы отургузулду! Акча менен сугарыңыз!"
        }
    elif progress_percent < 50:
        stage_texts = {
            'en': "🌿 Growing well! Add more to help it bloom!",
            'ru': "🌿 Хорошо растет! Добавь еще, чтобы он расцвел!",
            'kz': "🌿 Жақсы өсіп келеді! Гүлдеуіне көмектесіңіз!",
            'ua': "🌿 Добре росте! Додай ще, щоб він розцвів!",
            'ky': "🌿 Жакшы өсүп жатат! Гүлдөшүнө жардам бериңиз!"
        }
    elif progress_percent < 80:
        stage_texts = {
            'en': "🌸 Almost there! A little more and it will bloom!",
            'ru': "🌸 Почти готово! Еще немного и он расцветет!",
            'kz': "🌸 Дайындау! Таяз ғана қалды!",
            'ua': "🌸 Майже готово! Ще трохи і він розцвіте!",
            'ky': "🌸 Дээрлик даяр! Дагы бир аз жана ал гүлдөйт!"
        }
    elif progress_percent < 100:
        stage_texts = {
            'en': "🌼 So close! Just a bit more!",
            'ru': "🌼 Так близко! Еще чуть-чуть!",
            'kz': "🌼 Жақында! Таяз ғана қалды!",
            'ua': "🌼 Так близько! Ще трохи!",
            'ky': "🌼 Ушунчалык жакын! Дагы бир аз!"
        }
    else:
        stage_texts = {
            'en': "🌸🌸🌸 FULLY BLOOMED! Congratulations! 🎉",
            'ru': "🌸🌸🌸 ПОЛНОСТЬЮ РАСЦВЕЛ! Поздравляем! 🎉",
            'kz': "🌸🌸🌸 ТОЛЫҚ ГҮЛДЕДІ! Құттықтаймыз! 🎉",
            'ua': "🌸🌸🌸 ПОВНІСТЮ РОЗЦВІВ! Вітаємо! 🎉",
            'ky': "🌸🌸🌸 ТОЛУК ГҮЛДӨДҮ! Куттуктайбыз! 🎉"
        }
    
    # Если язык не найден, используем английский
    stage_text = stage_texts.get(lang, stage_texts['en'])
    
    text = f"{flower_art}\n\n"
    text += f"🎯 <b>{plant_name}</b>\n"
    text += f"💰 {current:,.0f} / {target:,.0f} {currency_symbol}\n"
    text += f"📊 Progress: {progress_percent:.1f}%\n"
    text += f"{progress_bar}\n\n"
    text += f"💚 {stage_text}"
    
    return text


def get_plant_choice_keyboard(lang):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    # Если язык не найден, используем английский
    if f'name_{lang}' not in PLANT_TYPES['lotus']:
        lang = 'en'
    
    buttons = []
    for plant_key in ['lotus', 'rose', 'sunflower', 'bamboo', 'hibiscus']:
        plant_name = PLANT_TYPES[plant_key][f'name_{lang}']
        buttons.append([KeyboardButton(text=plant_name)])
    
    buttons.append([KeyboardButton(text="❌ Cancel")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)