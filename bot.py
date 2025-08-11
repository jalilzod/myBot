# === Part 1: imports, env, clients, i18n, base state ===
import os
import re
import math
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # required

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing in .env")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing in .env (needed for all DB access)")

# Admin IDs (comma-separated numeric IDs in .env)
ADMIN_IDS = set(
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
)

# Telegram bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Single Supabase client with service role key for ALL operations
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
supabase_admin = supabase  # alias for clarity if needed

# ===== i18n (translations) =====
LANG = {
    "ru": {
        "welcome": "Добро пожаловать в Yasroikard Logistic!",
        "menu_title": "Главное меню:",
        "btn_channels": "🛍 Наши каналы",
        "btn_track": "🔍 Отслеживание",
        "btn_calc": "📦 Расчёт объёма",
        "btn_eta": "🚚 Сроки доставки",
        "btn_about": "ℹ️ О нас",
        "btn_contact": "📞 Контакты",
        "btn_lang": "🌐 Язык",
        "btn_admin": "🛠 Админ",
        "btn_back": "⬅️ Назад",
        "btn_by_code": "🔢 По трек-коду",
        "btn_by_phone": "📞 По телефону",
        "btn_calc_again": "🔁 Новый расчёт",
        "btn_menu_back": "⬅️ В меню",

        "lang_pick": "Выберите язык:",
        "lang_saved": "Язык сохранён: {lang_name}",
        "channels_title": "Наши каналы:",
        "track_how": "Как искать отправление?",
        "track_enter_code": "Введите *трек-код* (например, YA123456789):",
        "track_enter_phone": "Введите *номер телефона* (например, +992XXXXXXXXX):",
        "search_none": "Ничего не найдено. Проверьте данные и попробуйте снова.",
        "search_again": "Ещё поиск? Выберите способ:",

        # Office address + about
        "about_text": (
            "🌏 **О нас — Yasroikard Logistic**\n\n"
            "🏢 **Адрес офиса:**\n"
            "Китай, провинция Чжэцзян, город Иу,\n"
            "улица Цзяндун, район Уай Синь Цунь,\n"
            "д. 44 / блок 1, офис B301\n\n"
            "👤 **Админы:** Yasroikard и Джалилов Киёмиддин\n\n"
            "💼 **Кто мы:** Профессиональные байеры в Китае. Поможем найти товар, проверить качество и сопровождать вас как переводчики — быстро, безопасно и эффективно.\n\n"
            "🛒 **Что предлагаем:**\n"
            "• Закупки для Wildberries, Ozon и др. онлайн/офлайн магазинов\n"
            "• Комиссия всего 5%\n"
            "• Контроль сделки от поиска до доставки\n\n"
            "🚢 **Доставка:**\n"
            "• Таджикистан: 18–26 дней\n"
            "• Россия: 13–18 дней\n"
            "• Европа и США: уточняйте у администратора\n\n"
            "💰 **Тарифы:** от 0,5 $/кг и от 190 $/м³\n\n"
            "🌍 Клиенты по всему миру: Азия, Европа, США, арабские страны, Африка.\n\n"
            "✨ Выбирайте нас и начните путь к предпринимательству!"
        ),
        "delivery_text": (
            "🚚 *Сроки доставки*\n\n"
            "📍 *Таджикистан:* 18–26 дней\n"
            "📍 *Россия:* 13–18 дней\n"
            "📍 *Европа и США:* уточняйте у администратора\n\n"
            "🏢 *Наш адрес:*\n"
            "Китай, провинция Чжэцзян, г\\. Иу,\n"
            "ул ЦзянДун, р-н УАй Синь Цунь,\n"
            "д 44  блок 1, офис B301\n\n"
            "💬 Для других стран свяжитесь с админом: @mg19981 или @Yasin\\_direct"
        ),

        "contact_text": (
            "📞 **Контакты**\n\n"
            "Админы: @mg19981 • @Yasin\\_direct\n\n"
            "🏢 **Адрес офиса:**\n"
            "Китай, провинция Чжэцзян, город Иу,\n"
            "улица Цзяндун, район Уай Синь Цунь,\n"
            "д 44  блок 1, офис B301"
        ),

                # inside LANG["ru"]
        "btn_warehouse": "🏭 Адреса складов",

        "warehouse_title_multi": "🏭 Адреса складов",
        "warehouse_tj_label": "Таджикистан",
        "warehouse_ru_label": "Россия",

        "warehouse_tj_address": (
            "收货人：YASCARGO\n"
            "电话：13661799136\n"
            "详细地址：浙江省 金华市 义乌市福田物流园A8-165号 (номери телефони хдтон)"
        ),
        "warehouse_ru_address": (
            "收货人：M9613-чор раками охири номер\n"
            "电话：15734838888\n"
            "详细地址：浙江省金华市义乌市 福田工业区涌金大道B9号院内9399库房M9613-чор раками охири номер"
        ),

        # one message, two code blocks for easy copy
        "warehouse_text_multi": (
            "*{title}*\n\n"
            "📦 *{tj_label}*\n"
            "```\n{tj_addr}\n```\n"
            "📦 *{ru_label}*\n"
            "```\n{ru_addr}\n```\n"
            "📌 Скопируйте нужный адрес."
        ),



        # Calculator i18n
        "calc_intro": "📦 Расчёт объёма (м³).\nСначала выберите единицы измерения:",
        "calc_enter_h_m": "Введите *высоту* в метрах (например, 1.2):",
        "calc_enter_h_cm": "Введите *высоту* в сантиметрах (например, 120):",
        "calc_enter_w_unit": "Ок. Теперь введите *ширину* в {unit_phrase}:",
        "calc_enter_l_unit": "Отлично. Теперь введите *длину* в {unit_phrase}:",
        "calc_invalid_value_unit": "Неверное значение. Введите {dimension} в {unit}.",
        "calc_result": "📦 Объём: *{volume:.3f} м³*",
        "unit_phrase_m": "метрах",
        "unit_phrase_cm": "сантиметрах",
        "unit_m": "м",
        "unit_cm": "см",
        "dim_height": "высоту",
        "dim_width": "ширину",
        "dim_length": "длину",
    },
    "en": {
        "welcome": "Welcome to Yasroikard Logistic!",
        "menu_title": "Main menu:",
        "btn_channels": "🛍 Our channels",
        "btn_track": "🔍 Tracking",
        "btn_calc": "📦 Volume calculator",
        "btn_eta": "🚚 Delivery time",
        "btn_about": "ℹ️ About us",
        "btn_contact": "📞 Contacts",
        "btn_lang": "🌐 Language",
        "btn_admin": "🛠 Admin",
        "btn_back": "⬅️ Back",
        "btn_by_code": "🔢 By tracking code",
        "btn_by_phone": "📞 By phone",
        "btn_calc_again": "🔁 New calculation",
        "btn_menu_back": "⬅️ Main menu",

        "lang_pick": "Choose your language:",
        "lang_saved": "Language saved: {lang_name}",
        "channels_title": "Our channels:",
        "track_how": "How would you like to search?",
        "track_enter_code": "Enter *tracking code* (e.g., YA123456789):",
        "track_enter_phone": "Enter *phone number* (e.g., +1XXXXXXXXXX):",
        "search_none": "No results. Please check and try again.",
        "search_again": "Search again? Choose a method:",

        "about_text": (
            "🌏 **About Yasroikard Logistic**\n\n"
            "🏢 **Office address:**\n"
            "Yiwu City, Jiangdong Street, Wài Xīn Cūn area,\n"
            "Building 44 / Block 1, Office B301, Zhejiang, China\n\n"
            "👤 **Admins:** Yasroikard and Jalilov Kiyomidin\n\n"
            "💼 **Who we are:** Professional buyers in China. We help you find products, inspect quality, and act as interpreters — fast, safe, and efficient.\n\n"
            "🛒 **What we offer:**\n"
            "• Purchasing for Wildberries, Ozon and more (online/offline)\n"
            "• Commission only 5%\n"
            "• Deal control from sourcing to delivery\n\n"
            "🚢 **Delivery:**\n"
            "• Tajikistan: 18–26 days\n"
            "• Russia: 13–18 days\n"
            "• Europe & USA: ask the admin\n\n"
            "💰 **Rates:** from $0.5/kg and from $190/m³\n\n"
            "🌍 Clients worldwide: Asia, Europe, USA, Arab countries, Africa.\n\n"
            "✨ Choose us and start your business journey!"
        ),

        # Warehouse (EN)
        "btn_warehouse": "🏭 Warehouse addresses",

        "warehouse_title_multi": "🏭 Warehouse addresses",
        "warehouse_tj_label": "Tajikistan",
        "warehouse_ru_label": "Russia",

        "warehouse_tj_address": (
            "收货人：YASCARGO\n"
            "电话：13661799136\n"
            "详细地址：浙江省 金华市 义乌市福田物流园A8-165号 (номери телефони хдтон)"
        ),
        "warehouse_ru_address": (
            "收货人：M9613-чор раками охири номер\n"
            "电话：15734838888\n"
            "详细地址：浙江省金华市义乌市 福田工业区涌金大道B9号院内9399库房M9613-чор раками охири номер"
        ),

        "warehouse_text_multi": (
            "*{title}*\n\n"
            "📦 *{tj_label}*\n"
            "```\n{tj_addr}\n```\n"
            "📦 *{ru_label}*\n"
            "```\n{ru_addr}\n```\n"
            "📌 Copy the address you need."
        ),


        "delivery_text": (
            "🚚 *Delivery times*\n\n"
            "📍 *Tajikistan:* 18–26 days\n"
            "📍 *Russia:* 13–18 days\n"
            "📍 *Europe & USA:* check with admin\n\n"
            "🏢 *Our address:*\n"
            "China, Zhejiang Province, Yiwu City,\n"
            "JiangDong Street, WuAi XinCun District,\n"
            "No 44  Block 1, Office B301\n\n"
            "💬 For other countries contact admin: @mg19981 or @Yasin\\_direct"
        ),

        "contact_text": (
            "📞 **Contacts**\n\n"
            "Admins: @mg19981 • @Yasin\\_direct\n\n"
            "🏢 **Office address:**\n"
            "Yiwu City, Jiangdong Street, Wài Xīn Cūn area,\n"
            "Building 44  Block 1, Office B301, Zhejiang, China"
        ),

        "calc_intro": "📦 Volume calculator (m³).\nFirst, choose the units:",
        "calc_enter_h_m": "Enter *height* in meters (e.g., 1.2):",
        "calc_enter_h_cm": "Enter *height* in centimeters (e.g., 120):",
        "calc_enter_w_unit": "Great. Now enter *width* in {unit_phrase}:",
        "calc_enter_l_unit": "Perfect. Finally enter *length* in {unit_phrase}:",
        "calc_invalid_value_unit": "Invalid value. Please enter {dimension} in {unit}.",
        "calc_result": "📦 Volume: *{volume:.3f} m³*",
        "unit_phrase_m": "meters",
        "unit_phrase_cm": "centimeters",
        "unit_m": "m",
        "unit_cm": "cm",
        "dim_height": "height",
        "dim_width": "width",
        "dim_length": "length",
    },
    "tj": {
        "welcome": "Хуш омадед ба Yasroikard Logistic!",
        "menu_title": "Менюи асосӣ:",
        "btn_channels": "🛍 Каналҳои мо",
        "btn_track": "🔍 Пайгирӣ",
        "btn_calc": "📦 Ҳисоби ҳаҷм",
        "btn_eta": "🚚 Мӯҳлати расонӣ",
        "btn_about": "ℹ️ Дар бораи мо",
        "btn_contact": "📞 Тамос",
        "btn_lang": "🌐 Забон",
        "btn_admin": "🛠 Админ",
        "btn_back": "⬅️ Бозгашт",
        "btn_by_code": "🔢 Аз рӯи код",
        "btn_by_phone": "📞 Аз рӯи телефон",
        "btn_calc_again": "🔁 Ҳисоби нав",
        "btn_menu_back": "⬅️ Ба меню",

        "lang_pick": "Забонро интихоб кунед:",
        "lang_saved": "Забон нигоҳ дошта шуд: {lang_name}",
        "channels_title": "Каналҳои мо:",
        "track_how": "Чӣ тавр ҷустуҷӯ мекунед?",
        "track_enter_code": "Рамзи *трек*-ро ворид кунед:",
        "track_enter_phone": "Рақами *телефон*-ро ворид кунед:",
        "search_none": "Ёфт нашуд. Санҷед ва боз кӯшиш кунед.",
        "search_again": "Боз ҷустуҷӯ мекунед? Усулро интихоб кунед:",

        "about_text": (
            "🌏 **Дар бораи Yasroikard Logistic**\n\n"
            "🏢 **Суроғаи офис:**\n"
            "Шаҳри Йиву, кӯч. Ҷяндун, маҳ. Вай Син Чун,\n"
            "Бинои 44 / Қисми 1, утоқ B301, Вил. Ҷेजян, Чин\n\n"
            "👤 **Админҳо:** Yasroikard ва Ҷалилов Қиёмиддин\n\n"
            "💼 **Мо кистем:** Харидорони касбӣ дар Чин. Дар пайдо кардани мол, санҷиши сифат ва тарҷумонӣ ба шумо кӯмак мерасонем — зуд, бехатар ва муассир.\n\n"
            "🛒 **Хизматҳо:**\n"
            "• Харид барои Wildberries, Ozon ва ғ.\n"
            "• Комиссия танҳо 5%\n"
            "• Назорати муомила аз ҷустуҷӯ то расонидан\n\n"
            "🚢 **Расонидан:**\n"
            "• Тоҷикистон: 18–26 рӯз\n"
            "• Русия: 13–18 рӯз\n"
            "• Аврупо ва ИМА: бо админ равшан кунед\n\n"
            "💰 **Тарифҳо:** аз $0.5/кг ва аз $190/м³\n\n"
            "🌍 Мизоҷон аз тамоми ҷаҳон.\n\n"
            "✨ Бо мо оғоз кунед!"
        ),


        # Warehouse (TJ)
        "btn_warehouse": "🏭 Нишонии анборҳо",

        "warehouse_title_multi": "🏭 Нишонии анборҳо",
        "warehouse_tj_label": "Тоҷикистон",
        "warehouse_ru_label": "Русия",

        "warehouse_tj_address": (
            "收货人：YASCARGO\n"
            "电话：13661799136\n"
            "详细地址：浙江省 金华市 义乌市福田物流园A8-165号 (номери телефони хдтон)"
        ),
        "warehouse_ru_address": (
            "收货人：M9613-чор раками охири номер\n"
            "电话：15734838888\n"
            "详细地址：浙江省金华市义乌市 福田工业区涌金大道B9号院内9399库房M9613-чор раками охири номер"
        ),

        "warehouse_text_multi": (
            "*{title}*\n\n"
            "📦 *{tj_label}*\n"
            "```\n{tj_addr}\n```\n"
            "📦 *{ru_label}*\n"
            "```\n{ru_addr}\n```\n"
            "📌 Нишониро аз боло нусха кунед."
        ),


        "delivery_text": (
            "🚚 *Мӯҳлати расонӣ*\n\n"
            "📍 *Тоҷикистон:* 18–26 рӯз\n"
            "📍 *Русия:* 13–18 рӯз\n"
            "📍 *Аврупо ва ИМА:* бо админ санҷед\n\n"
            "🏢 *Суроғаи мо:*\n"
            "Чин, вилояти Чжэцзян, шаҳри Иу,\n"
            "кӯчаи ЦзянДун, ноҳияи УАй Синь Цунь,\n"
            "хона 44  блок 1, утоқи B301\n\n"
            "💬 Барои дигар кишварҳо бо админ тамос гиред: @mg19981 ё @Yasin\\_direct"
        ),

        "contact_text": (
            "📞 **Тамос**\n\n"
            "Админҳо: @mg19981 • @Yasin\\_direct\n\n"
            "🏢 **Суроғаи офис:**\n"
            "Шаҳри Йиву, кӯч. Ҷяндун, маҳ. Вай Син Чун,\n"
            "Бинои 44  Қисми 1, утоқ B301, Вил. Ҷежян, Чин"
        ),

        "calc_intro": "📦 Ҳисоби ҳаҷм (м³).\nАввал воҳидҳоро интихоб кунед:",
        "calc_enter_h_m": "Баландиро *дар метр* ворид кунед (масалан, 1.2):",
        "calc_enter_h_cm": "Баландиро *дар сантиметр* ворид кунед (масалан, 120):",
        "calc_enter_w_unit": "Хуб. Акнун *бар*-ро дар {unit_phrase} ворид кунед:",
        "calc_enter_l_unit": "Аъло. Ниҳоят *дарозӣ*-ро дар {unit_phrase} ворид кунед:",
        "calc_invalid_value_unit": "Қимати нодуруст. {dimension}-ро дар {unit} ворид кунед.",
        "calc_result": "📦 Ҳаҷм: *{volume:.3f} м³*",
        "unit_phrase_m": "метрҳо",
        "unit_phrase_cm": "сантиметрҳо",
        "unit_m": "м",
        "unit_cm": "см",
        "dim_height": "баландӣ",
        "dim_width": "бар",
        "dim_length": "дарозӣ",
    },
}
LANG_NAMES = {"ru": "Русский", "en": "English", "tj": "Тоҷикӣ"}

USER_LANG_CACHE: dict[int, str] = {}
def get_lang(user_id: int) -> str:
    lang = USER_LANG_CACHE.get(user_id)
    if lang:
        return lang
    try:
        r = supabase.table("users").select("language").eq("id", user_id).limit(1).execute()
        lang = (r.data or [{}])[0].get("language") or "ru"
    except Exception:
        lang = "ru"
    # Safety: normalize bad legacy values
    if lang not in LANG:
        lang = "ru"
    USER_LANG_CACHE[user_id] = lang
    return lang

def set_lang(user_id: int, lang: str):
    USER_LANG_CACHE[user_id] = lang
    try:
        supabase.table("users").update({"language": lang}).eq("id", user_id).execute()
    except Exception as e:
        print("set_lang error:", e)

def t(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    base = LANG.get(lang, LANG["ru"])
    txt = base.get(key, LANG["ru"].get(key, key))
    if kwargs:
        txt = txt.format(**kwargs)
    return txt

# Base states
ADMIN_FLOW_STATE: dict[int, str | None] = {}
ADMIN_NEW_SHIPMENT: dict[int, dict] = {}
USER_TRACK_STATE: dict[int, bool] = {}
USER_TRACK_MODE: dict[int, str] = {}
ADMIN_STATUS_STATE: dict[int, str | None] = {}
ADMIN_STATUS_TARGET: dict[int, str] = {}
USER_REQ_STATE: dict[int, str | None] = {}
USER_REQ_DATA: dict[int, dict] = {}
ADMIN_REQ_CONTEXT: dict[int, int | None] = {}
PAGE_SIZE = 10
ADMIN_LIST_PAGE: dict[int, int] = {}
CALC_STATE: dict[int, str | None] = {}
CALC_DATA: dict[int, dict] = {}
# Benefit flow (admin)
BEN_STATE: dict[int, str | None] = {}   # "whatsapp"|"ordered"|"paid"|"real_cost"|"user_paid"|None
BEN_DATA: dict[int, dict] = {}          # temp: {"whatsapp": str, "ordered": bool, "paid": bool, "real_cost": float, "user_paid": float}
# Benefits list paging
BEN_PAGE_SIZE = 10
ADMIN_BEN_PAGE: dict[int, int] = {}  # admin_user_id -> current page (1-based)

STATUS_OPTIONS = {"in_transit": "В пути", "arrived": "Прибыло", "warehouse": "На складе"}
PHONE_RE = re.compile(r"^\+?\d{7,15}$")
def normalize_phone(p: str) -> str:
    p = p.strip().replace(" ", "").replace("-", "")
    if p.startswith("+"):
        return "+" + re.sub(r"\D", "", p)
    return re.sub(r"\D", "", p)
def is_phone(text: str) -> bool:
    t_ = text.strip().replace(" ", "").replace("-", "")
    return t_.startswith("+") or t_.isdigit()






############################################################################
############################################################################

# === Part 2: keyboards + calculator helpers ===
def main_menu_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=L["btn_channels"], callback_data="menu:channels"),
            InlineKeyboardButton(text=L["btn_track"], callback_data="menu:track"),
        ],
        [
            InlineKeyboardButton(text=L["btn_calc"], callback_data="menu:calc"),
            InlineKeyboardButton(text=L["btn_eta"], callback_data="menu:delivery"),
        ],
        [
            InlineKeyboardButton(text=L["btn_about"], callback_data="menu:about"),
            InlineKeyboardButton(text=L["btn_contact"], callback_data="menu:contact"),
        ],
        [
            InlineKeyboardButton(text=L["btn_warehouse"], callback_data="menu:warehouse"),
        ],

        [
            InlineKeyboardButton(text=L["btn_lang"], callback_data="menu:lang"),
            InlineKeyboardButton(text=L["btn_admin"], callback_data="menu:admin"),
        ],
    ])

def channels_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Одежда", url="https://t.me/yasroikard_gr")],
        [InlineKeyboardButton(text="📱 Электроника", url="https://t.me/yasroikard_elektronika")],
        [InlineKeyboardButton(text="🕰 Часы и аксессуары", url="https://t.me/russiamanwatchs")],
        [InlineKeyboardButton(text=L["btn_back"], callback_data="menu:back")]
    ])

def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить отправление", callback_data="admin:add")],
        [InlineKeyboardButton(text="🔍 Поиск (тел/трек)", callback_data="admin:search")],
        [InlineKeyboardButton(text="📄 Все отправления", callback_data="admin:list")],
        [InlineKeyboardButton(text="✏️ Изменить статус", callback_data="admin:status")],
        [InlineKeyboardButton(text="📝 Заявки (польз.)", callback_data="admin:reqs")],
        [InlineKeyboardButton(text="💹 Benefit (учёт прибыли)", callback_data="admin:benefit")],
        [InlineKeyboardButton(text="📊 Benefits (статистика)", callback_data="admin:benefits")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")],
    ])

def track_choice_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=L["btn_by_code"], callback_data="track:by_code"),
            InlineKeyboardButton(text=L["btn_by_phone"], callback_data="track:by_phone"),
        ],
        [InlineKeyboardButton(text=L["btn_back"], callback_data="menu:back")]
    ])

def ben_list_nav_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data="benlist:prev"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="➡️ След.", callback_data="benlist:next"))
    if not row:
        row = [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:benefits")]
    return InlineKeyboardMarkup(inline_keyboard=[
        row,
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:admin")],
    ])

def status_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚚 В пути", callback_data="status:set:in_transit"),
            InlineKeyboardButton(text="🛬 Прибыло", callback_data="status:set:arrived"),
        ],
        [
            InlineKeyboardButton(text="🏷 На складе", callback_data="status:set:warehouse"),
            InlineKeyboardButton(text="⬅️ Отмена", callback_data="status:cancel"),
        ],
    ])

def phone_code_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="+992", callback_data="req:code:+992"),
            InlineKeyboardButton(text="+7", callback_data="req:code:+7"),
            InlineKeyboardButton(text="+1", callback_data="req:code:+1"),
            InlineKeyboardButton(text="+44", callback_data="req:code:+44"),
        ],
        [InlineKeyboardButton(text="✏️ Свой код", callback_data="req:code:custom")],
    ])

def country_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Tajikistan", callback_data="req:country:Tajikistan"),
            InlineKeyboardButton(text="Russia", callback_data="req:country:Russia"),
        ],
        [
            InlineKeyboardButton(text="Kazakhstan", callback_data="req:country:Kazakhstan"),
            InlineKeyboardButton(text="USA", callback_data="req:country:USA"),
        ],
        [
            InlineKeyboardButton(text="EU", callback_data="req:country:EU"),
            InlineKeyboardButton(text="✏️ Другая страна", callback_data="req:country:custom"),
        ],
    ])

def request_review_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"req:approve:{req_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"req:reject:{req_id}"),
        ],
        [InlineKeyboardButton(text="➡️ Следующая заявка", callback_data="req:next")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:admin")],
    ])

def lang_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:set:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:set:en"),
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang:set:tj"),
        ],
        [InlineKeyboardButton(text=L["btn_back"], callback_data="menu:back")]
    ])

def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"{prefix}:yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"{prefix}:no"),
        ],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="ben:cancel")],
    ])

def benefit_menu_btn_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="menu:admin")],
    ])

# Calculator helpers (localized prompts)
def calc_unit_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Метры (м)", callback_data="calc:unit:m"),
            InlineKeyboardButton(text="Сантиметры (см)", callback_data="calc:unit:cm"),
        ],
        [InlineKeyboardButton(text=L["btn_back"], callback_data="menu:back")],
    ])

def calc_again_kb(lang_code: str) -> InlineKeyboardMarkup:
    L = LANG.get(lang_code, LANG["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=L["btn_calc_again"], callback_data="menu:calc")],
        [InlineKeyboardButton(text=L["btn_menu_back"], callback_data="menu:back")],
    ])

def _parse_pos_float(s: str) -> float | None:
    try:
        s = s.replace(",", ".").strip()
        v = float(s)
        return v if v > 0 else None
    except:
        return None



###############################################################################
###############################################################################



# === Part 3: DB helpers (search/save/list) ===
def format_shipment_row(row: dict) -> str:
    parts = [
        f"Трек: {row.get('tracking_code')}",
        f"Тел: {row.get('phone') or '—'}",
        f"Статус: {row.get('status') or '—'}",
    ]
    if row.get("description"):
        parts.append(f"Описание: {row['description']}")
    return "\n".join(parts)

def format_request_row(r: dict) -> str:
    return (
        f"Заявка #{r.get('id')}\n"
        f"Пользователь: {r.get('user_id')}\n"
        f"Трек: {r.get('tracking_code')}\n"
        f"Тел: {r.get('phone')}\n"
        f"Страна: {r.get('country')}\n"
        f"Статус: {r.get('status')}"
    )

async def find_shipments(query: str, mode: str | None = None) -> list[dict]:
    q = query.strip()
    try:
        if mode == "phone":
            res = supabase.table("shipments").select("*").eq("phone", normalize_phone(q)).order("created_at", desc=True).limit(20).execute()
        elif mode == "code":
            res = supabase.table("shipments").select("*").eq("tracking_code", q).limit(5).execute()
        else:
            if is_phone(q):
                res = supabase.table("shipments").select("*").eq("phone", normalize_phone(q)).order("created_at", desc=True).limit(20).execute()
            else:
                res = supabase.table("shipments").select("*").eq("tracking_code", q).limit(5).execute()
        return res.data or []
    except Exception as e:
        print("Search error:", e)
        return []

async def save_shipment_to_db(data: dict) -> tuple[bool, str]:
    tracking = data.get("tracking_code")
    phone = data.get("phone")
    description = data.get("description")
    try:
        dup = supabase_admin.table("shipments").select("id").eq("tracking_code", tracking).limit(1).execute()
        if dup.data:
            return False, "❗ Отправление с таким трек-кодом уже существует."
    except Exception as e:
        return False, f"Ошибка проверки дубликата: {e}"
    try:
        ins = supabase_admin.table("shipments").insert({
            "tracking_code": tracking, "phone": phone, "description": description,
            "status": "В пути", "image_url": None,
        }).execute()
        return (True, "✅ Отправление сохранено.") if ins.data else (False, "Не удалось сохранить отправление.")
    except Exception as e:
        return False, f"Ошибка сохранения: {e}"

async def get_next_pending_request() -> dict | None:
    try:
        res = supabase_admin.table("shipment_requests").select("*").eq("status", "pending").order("created_at", desc=False).limit(1).execute()
        return (res.data or [None])[0]
    except Exception as e:
        print("Fetch pending request error:", e)
        return None

# ---------- Benefits (profit) helpers ----------
async def save_benefit_row(admin_id: int, data: dict) -> tuple[bool, str]:
    """
    Expects data = {
      "whatsapp": str, "ordered": bool, "paid": bool,
      "real_cost": float, "user_paid": float
    }
    """
    try:
        # Profit = user_paid - real_cost
        benefit = float(data["user_paid"]) - float(data["real_cost"])
        supabase_admin.table("order_benefits").insert({
            "tg_admin_id": admin_id,
            "whatsapp": data["whatsapp"],
            "ordered": data["ordered"],
            "paid": data["paid"],
            "real_cost": data["real_cost"],
            "user_paid": data["user_paid"],
            "benefit": benefit,
        }).execute()
        return True, f"💾 Сохранено. Прибыль: {benefit:.2f}."
    except Exception as e:
        return False, f"Ошибка сохранения: {e}"

# Pretty formatting (HTML monospace table)
def _fmt_money(x) -> str:
    try:
        # 12 345.67 style
        return f"{float(x):,.2f}".replace(",", " ")
    except:
        return "0.00"

def _pad(text: str, width: int) -> str:
    t = str(text or "")
    return t[:width].ljust(width)

def format_benefit_row_line(r: dict) -> str:
    wa = r.get("whatsapp") or "—"
    paid = "Да" if r.get("paid") else "Нет"
    rc  = _fmt_money(r.get("real_cost") or 0)
    up  = _fmt_money(r.get("user_paid") or 0)
    bf  = _fmt_money(r.get("benefit") or 0)
    dt  = (r.get("created_at") or "")[:19]
    return (
        f"{_pad(wa, 17)}  "
        f"{_pad(paid, 3)}  "
        f"{_pad(rc, 10)}  "
        f"{_pad(up, 10)}  "
        f"{_pad(bf, 10)}  "
        f"{_pad(dt, 19)}"
    )

async def fetch_benefits_page(page: int, page_size: int = BEN_PAGE_SIZE) -> tuple[list[dict], int]:
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    end = start + page_size - 1
    res = supabase_admin.table("order_benefits") \
        .select("id, whatsapp, paid, real_cost, user_paid, benefit, created_at", count="exact") \
        .order("created_at", desc=True).range(start, end).execute()
    rows = res.data or []
    total = res.count or 0
    return rows, total

async def fetch_benefits_totals() -> tuple[float, float, float]:
    try:
        res = supabase_admin.table("order_benefits").select("real_cost, user_paid, benefit").execute()
        items = res.data or []
        rc = sum(float(x.get("real_cost") or 0) for x in items)
        up = sum(float(x.get("user_paid") or 0) for x in items)
        bf = sum(float(x.get("benefit") or 0) for x in items)
        return rc, up, bf
    except Exception as e:
        print("Totals fetch error:", e)
        return 0.0, 0.0, 0.0

async def render_benefits_page(page: int) -> tuple[str, InlineKeyboardMarkup]:
    rows, total = await fetch_benefits_page(page)
    rc_sum, up_sum, bf_sum = await fetch_benefits_totals()

    total_pages = max(1, math.ceil((total or 0) / BEN_PAGE_SIZE))
    header = (
        "📊 <b>Учёт прибыли</b>\n"
        f"Страница {page}/{total_pages} • Записей: {total}\n"
    )

    table_header = (
        "<pre>"
        f"{_pad('WhatsApp', 17)}  "
        f"{_pad('Опл', 3)}  "
        f"{_pad('Реал.', 10)}  "
        f"{_pad('Оплач.', 10)}  "
        f"{_pad('Профит', 10)}  "
        f"{_pad('Дата', 19)}\n"
        f"{'-'*73}\n"
    )

    body = ""
    if total:
        body = "\n".join(format_benefit_row_line(r) for r in rows) + "\n"

    table_footer = (
        f"{'-'*73}\n"
        f"{_pad('ИТОГО:', 22)}  "
        f"{_pad(_fmt_money(rc_sum), 10)}  "
        f"{_pad(_fmt_money(up_sum), 10)}  "
        f"{_pad(_fmt_money(bf_sum), 10)}\n"
        "</pre>"
    )

    text = header + table_header + body + table_footer
    kb = ben_list_nav_kb(page, total_pages)
    return text, kb

async def show_admin_benefits(msg, admin_id: int, page: int):
    ADMIN_BEN_PAGE[admin_id] = page
    text, kb = await render_benefits_page(page)
    await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")

# ---------- Shipments list (unchanged) ----------
def format_ship_row_line(r: dict) -> str:
    tcode = r.get("tracking_code") or "—"
    s = r.get("status") or "—"
    p = r.get("phone") or "—"
    c = (r.get("created_at") or "")[:19]
    return f"{tcode} | {s} | {p} | {c}"

async def fetch_shipments_page(page: int, page_size: int = PAGE_SIZE) -> tuple[list[dict], int]:
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    end = start + page_size - 1
    res = supabase_admin.table("shipments").select("*", count="exact").order("created_at", desc=True).range(start, end).execute()
    return (res.data or []), (res.count or 0)

def list_nav_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data="list:prev"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="➡️ След.", callback_data="list:next"))
    if not row:
        row = [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:list")]
    rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def render_shipments_page(page: int) -> tuple[str, InlineKeyboardMarkup]:
    rows, total = await fetch_shipments_page(page)
    if total == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:admin")]])
        return "Пока нет отправлений.", kb
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    header = f"📄 Все отправления — страница {page}/{total_pages}\nПоказано: {len(rows)} из {total}"
    lines = [header, "```", "Трек | Статус | Телефон | Создано", "-" * 40]
    for r in rows:
        lines.append(format_ship_row_line(r))
    lines.append("```")
    return "\n".join(lines), list_nav_kb(page, total_pages)

async def show_admin_list(msg, admin_id: int, page: int):
    ADMIN_LIST_PAGE[admin_id] = page
    text, kb = await render_shipments_page(page)
    await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")




###############################################################################
###############################################################################


# === Part 4: callback handlers ===
@dp.message(CommandStart())
async def on_start(message: Message):
    user_row = {
        "id": message.from_user.id, "username": message.from_user.username,
        "phone": None, "role": "user", "language": "ru",
    }
    try:
        supabase.table("users").upsert(user_row, on_conflict="id").execute()
    except Exception as e:
        print("User upsert error:", e)
    uid = message.from_user.id
    await message.answer(t(uid, "welcome") + "\n" + t(uid, "menu_title"),
                         reply_markup=main_menu_kb(get_lang(uid)))

@dp.message(Command("menu"))
async def open_menu(message: Message):
    uid = message.from_user.id
    await message.answer(t(uid, "menu_title"), reply_markup=main_menu_kb(get_lang(uid)))

@dp.callback_query(F.data.startswith("menu:"))
async def handle_menu_callbacks(cb: CallbackQuery):
    key = cb.data.split(":", 1)[1]
    uid = cb.from_user.id
    lang = get_lang(uid)

    if key == "channels":
        await cb.message.edit_text(t(uid, "channels_title"), reply_markup=channels_kb(lang))
    elif key == "track":
        await cb.message.edit_text(t(uid, "track_how"), reply_markup=track_choice_kb(lang))
    elif key == "calc":
        CALC_STATE[uid] = "calc_unit"; CALC_DATA[uid] = {}
        await cb.message.edit_text(t(uid, "calc_intro"), reply_markup=calc_unit_kb(lang))
    elif key == "delivery":
        # FIX: use t() to avoid KeyError with legacy/nonstandard lang codes
        await cb.message.edit_text(t(uid, "delivery_text"), parse_mode="Markdown")
    elif key == "about":
        await cb.message.edit_text(t(uid, "about_text"), parse_mode="Markdown")
    elif key == "contact":
        await cb.message.edit_text(t(uid, "contact_text"), parse_mode="Markdown")
    elif key == "lang":
        await cb.message.edit_text(t(uid, "lang_pick"), reply_markup=lang_kb(lang))
    elif key == "warehouse":
        lang = get_lang(uid)
        L = LANG.get(lang, LANG["ru"])
        txt = L["warehouse_text_multi"].format(
            title=L["warehouse_title_multi"],
            tj_label=L["warehouse_tj_label"],
            ru_label=L["warehouse_ru_label"],
            tj_addr=L["warehouse_tj_address"],
            ru_addr=L["warehouse_ru_address"],
        )
        # code fences make it copy-friendly and avoid Markdown parse issues
        await cb.message.edit_text(txt, parse_mode="Markdown")

    elif key == "admin":
        if uid in ADMIN_IDS:
            await cb.message.edit_text("Админ-панель: выберите действие.", reply_markup=admin_menu_kb())
        else:
            await cb.message.edit_text("⛔ Доступ запрещён. Эта панель только для администраторов.")
    elif key == "req":
        USER_REQ_STATE[uid] = "req_track"; USER_REQ_DATA[uid] = {}
        await cb.message.edit_text("📥 Заявка на добавление отправления.\n\nВведите *трек-код*:", parse_mode="Markdown")
    elif key == "back":
        await cb.message.edit_text(t(uid, "menu_title"), reply_markup=main_menu_kb(lang))
    await cb.answer()

# Admin: Benefit flow start
@dp.callback_query(F.data == "admin:benefit")
async def admin_benefit_start(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    BEN_STATE[uid] = "whatsapp"
    BEN_DATA[uid] = {}
    await cb.message.edit_text(
        "💹 Учёт прибыли.\n\nВведите *WhatsApp клиента* (например, +992xxxxxxxxx или 8xxxxxxxxx):",
        parse_mode="Markdown"
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("ben:ordered:"))
async def ben_ordered_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS or BEN_STATE.get(uid) != "ordered":
        await cb.answer(); return
    val = cb.data.split(":")[2]  # yes|no
    BEN_DATA.setdefault(uid, {})["ordered"] = (val == "yes")
    BEN_STATE[uid] = "paid"
    await cb.message.edit_text("Покупатель оплатил заказ?\nВыберите вариант:", reply_markup=yes_no_kb("ben:paid"))
    await cb.answer()

@dp.callback_query(F.data.startswith("ben:paid:"))
async def ben_paid_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS or BEN_STATE.get(uid) != "paid":
        await cb.answer(); return
    val = cb.data.split(":")[2]  # yes|no
    BEN_DATA.setdefault(uid, {})["paid"] = (val == "yes")
    BEN_STATE[uid] = "real_cost"
    await cb.message.edit_text("Введите *реальную стоимость товара* (число):", parse_mode="Markdown")
    await cb.answer()

@dp.callback_query(F.data == "ben:cancel")
async def ben_cancel(cb: CallbackQuery):
    uid = cb.from_user.id
    BEN_STATE[uid] = None
    BEN_DATA[uid] = {}
    await cb.message.edit_text("Отменено. Админ-панель:", reply_markup=admin_menu_kb())
    await cb.answer()

# Language set
@dp.callback_query(F.data.startswith("lang:set:"))
async def set_language(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = cb.data.split(":")[2]
    if lang not in LANG:
        await cb.answer("Unsupported", show_alert=True); return
    set_lang(uid, lang)
    await cb.message.edit_text(
        t(uid, "lang_saved", lang_name=LANG_NAMES.get(lang, lang)) + "\n" + t(uid, "menu_title"),
        reply_markup=main_menu_kb(lang)
    )
    await cb.answer()

@dp.callback_query(F.data == "admin:benefits")
async def admin_benefits_start(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    await show_admin_benefits(cb.message, uid, page=1)
    await cb.answer()

@dp.callback_query(F.data == "benlist:prev")
async def ben_list_prev(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    current = max(2, ADMIN_BEN_PAGE.get(uid, 1))
    await show_admin_benefits(cb.message, uid, page=current - 1)
    await cb.answer()

@dp.callback_query(F.data == "benlist:next")
async def ben_list_next(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    current = max(1, ADMIN_BEN_PAGE.get(uid, 1))
    await show_admin_benefits(cb.message, uid, page=current + 1)
    await cb.answer()

# Track flow choice
@dp.callback_query(F.data == "track:by_code")
async def track_by_code(cb: CallbackQuery):
    USER_TRACK_STATE[cb.from_user.id] = True; USER_TRACK_MODE[cb.from_user.id] = "code"
    await cb.message.edit_text(t(cb.from_user.id, "track_enter_code"), parse_mode="Markdown"); await cb.answer()

@dp.callback_query(F.data == "track:by_phone")
async def track_by_phone(cb: CallbackQuery):
    USER_TRACK_STATE[cb.from_user.id] = True; USER_TRACK_MODE[cb.from_user.id] = "phone"
    await cb.message.edit_text(t(cb.from_user.id, "track_enter_phone"), parse_mode="Markdown"); await cb.answer()

# Calculator unit selection
@dp.callback_query(F.data == "calc:unit:m")
async def calc_unit_m(cb: CallbackQuery):
    u = cb.from_user.id; CALC_STATE[u] = "calc_h"; CALC_DATA.setdefault(u, {})["unit"] = "m"
    await cb.message.edit_text(t(u, "calc_enter_h_m"), parse_mode="Markdown"); await cb.answer()

@dp.callback_query(F.data == "calc:unit:cm")
async def calc_unit_cm(cb: CallbackQuery):
    u = cb.from_user.id; CALC_STATE[u] = "calc_h"; CALC_DATA.setdefault(u, {})["unit"] = "cm"
    await cb.message.edit_text(t(u, "calc_enter_h_cm"), parse_mode="Markdown"); await cb.answer()

# Admin: search shortcut
@dp.callback_query(F.data == "admin:search")
async def admin_search_start(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    await cb.message.edit_text("Как искать отправление?", reply_markup=track_choice_kb(get_lang(cb.from_user.id))); await cb.answer()

# Admin: add shipment
@dp.callback_query(F.data == "admin:add")
async def admin_add_start(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    ADMIN_FLOW_STATE[cb.from_user.id] = "awaiting_tracking"; ADMIN_NEW_SHIPMENT[cb.from_user.id] = {}
    await cb.message.edit_text("➕ Добавление отправления.\n\nВведите *трек-код* (например, YA123456789):", parse_mode="Markdown")
    await cb.answer()

# Admin: change status
@dp.callback_query(F.data == "admin:status")
async def admin_status_start(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    ADMIN_STATUS_STATE[cb.from_user.id] = "awaiting_status_tracking"; ADMIN_STATUS_TARGET[cb.from_user.id] = ""
    await cb.message.edit_text("✏️ Изменение статуса.\n\nВведите *трек-код* отправления:", parse_mode="Markdown"); await cb.answer()

@dp.callback_query(F.data == "status:cancel")
async def status_cancel(cb: CallbackQuery):
    u = cb.from_user.id; ADMIN_STATUS_STATE[u] = None; ADMIN_STATUS_TARGET[u] = ""
    await cb.message.edit_text("Отменено. Админ-панель:", reply_markup=admin_menu_kb()); await cb.answer()

@dp.callback_query(F.data.startswith("status:set:"))
async def status_set(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    tracking = ADMIN_STATUS_TARGET.get(cb.from_user.id)
    if not tracking:
        await cb.answer("Не выбран трек-код. Начните заново через «✏️ Изменить статус».", show_alert=True); return
    key = cb.data.split(":", 2)[2]; new_status = STATUS_OPTIONS.get(key)
    if not new_status:
        await cb.answer("Неизвестный статус.", show_alert=True); return
    try:
        upd = supabase_admin.table("shipments").update({"status": new_status}).eq("tracking_code", tracking).execute()
        if upd.data:
            await cb.message.edit_text(f"✅ Статус обновлён.\nТрек: *{tracking}*\nНовый статус: *{new_status}*", parse_mode="Markdown", reply_markup=admin_menu_kb())
        else:
            await cb.message.edit_text("Не удалось обновить статус. Проверьте трек-код и попробуйте снова.", reply_markup=admin_menu_kb())
    except Exception as e:
        await cb.message.edit_text(f"Ошибка обновления статуса: {e}", reply_markup=admin_menu_kb())
    ADMIN_STATUS_TARGET[cb.from_user.id] = ""; ADMIN_STATUS_STATE[cb.from_user.id] = None
    await cb.answer()

# Admin: requests review
@dp.callback_query(F.data == "admin:reqs")
async def admin_reqs(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    req = await get_next_pending_request()
    if not req:
        await cb.message.edit_text("Нет новых заявок. 🎉", reply_markup=admin_menu_kb()); await cb.answer(); return
    ADMIN_REQ_CONTEXT[cb.from_user.id] = req["id"]
    await cb.message.edit_text("Заявка на добавление:\n\n" + format_request_row(req), reply_markup=request_review_kb(req["id"]))
    await cb.answer()

@dp.callback_query(F.data == "req:next")
async def req_next(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    req = await get_next_pending_request()
    if not req:
        await cb.message.edit_text("Нет новых заявок. 🎉", reply_markup=admin_menu_kb()); await cb.answer(); return
    ADMIN_REQ_CONTEXT[cb.from_user.id] = req["id"]
    await cb.message.edit_text("Заявка на добавление:\n\n" + format_request_row(req), reply_markup=request_review_kb(req["id"]))
    await cb.answer()

@dp.callback_query(F.data.startswith("req:approve:"))
async def req_approve(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    req_id = int(cb.data.split(":")[2])
    try:
        r = supabase_admin.table("shipment_requests").select("*").eq("id", req_id).limit(1).execute()
        req = (r.data or [None])[0]
        if not req or req.get("status") != "pending":
            await cb.message.edit_text("Заявка не найдена или уже обработана.", reply_markup=admin_menu_kb()); await cb.answer(); return
    except Exception as e:
        await cb.message.edit_text(f"Ошибка загрузки заявки: {e}", reply_markup=admin_menu_kb()); await cb.answer(); return
    try:
        supabase_admin.table("shipments").insert({
            "tracking_code": req["tracking_code"], "phone": req["phone"],
            "description": f"Страна: {req['country']}", "status": "В пути", "image_url": None,
        }).execute()
        supabase_admin.table("shipment_requests").update({"status": "approved"}).eq("id", req_id).execute()
    except Exception as e:
        await cb.message.edit_text(f"Ошибка подтверждения: {e}", reply_markup=admin_menu_kb()); await cb.answer(); return
    try:
        await bot.send_message(req["user_id"], f"✅ Ваша заявка одобрена!\nТеперь вы можете отслеживать отправление:\nТрек: {req['tracking_code']}\nТелефон: {req['phone']}")
    except Exception:
        pass
    await cb.message.edit_text("Заявка подтверждена и добавлена в отправления. ✅", reply_markup=admin_menu_kb()); await cb.answer()

@dp.callback_query(F.data.startswith("req:reject:"))
async def req_reject(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    req_id = int(cb.data.split(":")[2])
    try:
        supabase_admin.table("shipment_requests").update({"status": "rejected"}).eq("id", req_id).execute()
    except Exception as e:
        await cb.message.edit_text(f"Ошибка отклонения: {e}", reply_markup=admin_menu_kb()); await cb.answer(); return
    try:
        r = supabase_admin.table("shipment_requests").select("user_id").eq("id", req_id).limit(1).execute()
        req_user = (r.data or [None])[0]
        if req_user:
            await bot.send_message(req_user["user_id"], "❌ Ваша заявка отклонена. Проверьте данные и отправьте снова.")
    except Exception:
        pass
    await cb.message.edit_text("Заявка отклонена. ❌", reply_markup=admin_menu_kb()); await cb.answer()

# Admin list/pagination
@dp.callback_query(F.data == "admin:list")
async def admin_list_start(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    await show_admin_list(cb.message, cb.from_user.id, page=1); await cb.answer()

@dp.callback_query(F.data == "list:prev")
async def admin_list_prev(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    current = max(2, ADMIN_LIST_PAGE.get(cb.from_user.id, 1))
    await show_admin_list(cb.message, cb.from_user.id, page=current - 1); await cb.answer()

@dp.callback_query(F.data == "list:next")
async def admin_list_next(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    current = max(1, ADMIN_LIST_PAGE.get(cb.from_user.id, 1))
    await show_admin_list(cb.message, cb.from_user.id, page=current + 1); await cb.answer()


##############################################################
##############################################################

# === Part 5: message router + runner ===
@dp.message()
async def message_router(message: Message):
    uid = message.from_user.id
    lang = get_lang(uid)

    # Admin add shipment — step 1: tracking
    if uid in ADMIN_IDS and ADMIN_FLOW_STATE.get(uid) == "awaiting_tracking":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий."); return
        ADMIN_NEW_SHIPMENT[uid]["tracking_code"] = tracking
        ADMIN_FLOW_STATE[uid] = "awaiting_phone"
        await message.answer("📞 Введите *номер телефона* клиента:", parse_mode="Markdown")
        return

    # Step 2: phone
    if uid in ADMIN_IDS and ADMIN_FLOW_STATE.get(uid) == "awaiting_phone":
        phone_raw = (message.text or "").strip()
        phone = normalize_phone(phone_raw)
        if not PHONE_RE.match(phone):
            await message.answer("Неверный формат телефона."); return
        ADMIN_NEW_SHIPMENT[uid]["phone"] = phone
        ADMIN_FLOW_STATE[uid] = "awaiting_description"
        await message.answer("📝 Введите *краткое описание*:", parse_mode="Markdown")
        return

    # Step 3: description -> save
    if uid in ADMIN_IDS and ADMIN_FLOW_STATE.get(uid) == "awaiting_description":
        desc = (message.text or "").strip()
        if len(desc) < 3:
            await message.answer("Описание слишком короткое."); return
        ADMIN_NEW_SHIPMENT[uid]["description"] = desc
        ok, msg = await save_shipment_to_db(ADMIN_NEW_SHIPMENT[uid])
        ADMIN_FLOW_STATE[uid] = None; ADMIN_NEW_SHIPMENT[uid] = {}
        await message.answer(msg)
        await message.answer("Админ-панель:", reply_markup=admin_menu_kb())
        return

    # Admin change status: ask tracking
    if uid in ADMIN_IDS and ADMIN_STATUS_STATE.get(uid) == "awaiting_status_tracking":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий."); return
        try:
            res = supabase_admin.table("shipments").select("id, tracking_code, status")\
                .eq("tracking_code", tracking).limit(1).execute()
            if not res.data:
                await message.answer("❗ Не найдено."); return
        except Exception as e:
            await message.answer(f"Ошибка: {e}"); return
        ADMIN_STATUS_TARGET[uid] = tracking
        ADMIN_STATUS_STATE[uid] = None
        await message.answer(
            f"Текущий статус: {res.data[0].get('status') or '—'}\nВыберите новый статус:",
            reply_markup=status_choice_kb()
        )
        return

    # User request flow
    if USER_REQ_STATE.get(uid) == "req_track":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий."); return
        USER_REQ_DATA.setdefault(uid, {})["tracking_code"] = tracking
        USER_REQ_STATE[uid] = "req_phone_code"
        await message.answer("Выберите код страны:", reply_markup=phone_code_kb())
        return

    if USER_REQ_STATE.get(uid) == "req_phone_code_custom":
        code = (message.text or "").strip()
        if not code.startswith("+") or not re.sub(r"\D", "", code):
            await message.answer("Неверный код."); return
        USER_REQ_DATA.setdefault(uid, {})["phone_code"] = code
        USER_REQ_STATE[uid] = "req_phone_local"
        await message.answer(f"Код выбран: {code}\nВведите номер без кода:")
        return

    if USER_REQ_STATE.get(uid) == "req_phone_local":
        local = (message.text or "").strip().replace(" ", "").replace("-", "")
        code = USER_REQ_DATA[uid].get("phone_code", "")
        full = normalize_phone(code + local)
        if not PHONE_RE.match(full):
            await message.answer("Неверный телефон."); return
        USER_REQ_DATA[uid]["phone"] = full
        USER_REQ_STATE[uid] = "req_country"
        await message.answer("Выберите страну:", reply_markup=country_kb())
        return

    if USER_REQ_STATE.get(uid) == "req_country_custom":
        country = (message.text or "").strip()
        if len(country) < 2:
            await message.answer("Слишком короткое название."); return
        USER_REQ_DATA[uid]["country"] = country
        try:
            supabase_admin.table("shipment_requests").insert({
                "user_id": uid,
                "tracking_code": USER_REQ_DATA[uid]["tracking_code"],
                "phone": USER_REQ_DATA[uid]["phone"],
                "country": USER_REQ_DATA[uid]["country"],
            }).execute()
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
            USER_REQ_STATE[uid] = None; USER_REQ_DATA[uid] = {}; return
        USER_REQ_STATE[uid] = None; USER_REQ_DATA[uid] = {}
        await message.answer("✅ Заявка отправлена.")
        await message.answer(t(uid, "menu_title"), reply_markup=main_menu_kb(lang))
        return

    # Calculator: height
    if CALC_STATE.get(uid) == "calc_h":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = LANG[lang]["unit_m"] if CALC_DATA.get(uid, {}).get("unit") == "m" else LANG[lang]["unit_cm"]
            await message.answer(t(uid, "calc_invalid_value_unit", dimension=t(uid, "dim_height"), unit=unit)); return
        CALC_DATA[uid]["h"] = v
        CALC_STATE[uid] = "calc_w"
        await message.answer(t(uid, "calc_enter_w_unit", unit_phrase=t(uid, f"unit_phrase_{CALC_DATA[uid]['unit']}")), parse_mode="Markdown")
        return

    # Calculator: width
    if CALC_STATE.get(uid) == "calc_w":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = LANG[lang]["unit_m"] if CALC_DATA[uid]["unit"] == "m" else LANG[lang]["unit_cm"]
            await message.answer(t(uid, "calc_invalid_value_unit", dimension=t(uid, "dim_width"), unit=unit)); return
        CALC_DATA[uid]["w"] = v
        CALC_STATE[uid] = "calc_l"
        await message.answer(t(uid, "calc_enter_l_unit", unit_phrase=t(uid, f"unit_phrase_{CALC_DATA[uid]['unit']}")), parse_mode="Markdown")
        return

    # Calculator: length
    if CALC_STATE.get(uid) == "calc_l":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = LANG[lang]["unit_m"] if CALC_DATA[uid]["unit"] == "m" else LANG[lang]["unit_cm"]
            await message.answer(t(uid, "calc_invalid_value_unit", dimension=t(uid, "dim_length"), unit=unit)); return
        CALC_DATA[uid]["l"] = v
        h, w, l_ = CALC_DATA[uid]["h"], CALC_DATA[uid]["w"], CALC_DATA[uid]["l"]
        if CALC_DATA[uid]["unit"] == "cm":
            h, w, l_ = h/100, w/100, l_/100
        volume = h * w * l_
        CALC_STATE[uid] = None; CALC_DATA[uid] = {}
        await message.answer(t(uid, "calc_result", volume=volume), parse_mode="Markdown",
                             reply_markup=calc_again_kb(lang))
        return

    # Admin benefit flow
    if uid in ADMIN_IDS and BEN_STATE.get(uid) == "whatsapp":
        wa = (message.text or "").strip()
        if not re.search(r"\d", wa):
            await message.answer("Неверный формат WhatsApp."); return
        BEN_DATA.setdefault(uid, {})["whatsapp"] = wa
        BEN_STATE[uid] = "ordered"
        await message.answer("Покупатель оформил заказ?", reply_markup=yes_no_kb("ben:ordered"))
        return

    if uid in ADMIN_IDS and BEN_STATE.get(uid) == "real_cost":
        val = _parse_pos_float(message.text or "")
        if val is None:
            await message.answer("Введите корректное число."); return
        BEN_DATA.setdefault(uid, {})["real_cost"] = float(val)
        BEN_STATE[uid] = "user_paid"
        await message.answer("Введите сумму, которую оплатил покупатель:")
        return

    if uid in ADMIN_IDS and BEN_STATE.get(uid) == "user_paid":
        val = _parse_pos_float(message.text or "")
        if val is None:
            await message.answer("Введите корректное число."); return
        BEN_DATA.setdefault(uid, {})["user_paid"] = float(val)
        ok, msg = await save_benefit_row(uid, BEN_DATA[uid])
        BEN_STATE[uid] = None; BEN_DATA[uid] = {}
        await message.answer(msg, reply_markup=benefit_menu_btn_kb())
        return

    # Tracking search flow
    if USER_TRACK_STATE.get(uid):
        query = (message.text or "").strip()
        if not query:
            await message.answer("Пустой запрос."); return
        mode = USER_TRACK_MODE.get(uid)
        results = await find_shipments(query, mode)
        USER_TRACK_STATE[uid] = False; USER_TRACK_MODE[uid] = ""
        if not results:
            await message.answer(t(uid, "search_none"))
            await message.answer(t(uid, "search_again"), reply_markup=track_choice_kb(lang))
            return
        if len(results) == 1:
            await message.answer(format_shipment_row(results[0]))
        else:
            await message.answer("\n\n".join(format_shipment_row(r) for r in results))
        await message.answer(t(uid, "search_again"), reply_markup=track_choice_kb(lang))
        return

# Runner
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



