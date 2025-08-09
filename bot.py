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

# Env
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY missing in .env")
if not SUPABASE_SERVICE_ROLE_KEY:
    print("⚠️ Warning: SUPABASE_SERVICE_ROLE_KEY missing — admin writes may fail if RLS is enabled.")

# Admin IDs (comma-separated numeric IDs in .env)
ADMIN_IDS = set(int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit())

# Clients
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)

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
        "lang_pick": "Выберите язык:",
        "lang_saved": "Язык сохранён: {lang_name}",
        "channels_title": "Наши каналы:",
        "track_how": "Как искать отправление?",
        "track_enter_code": "Введите *трек-код* (например, YA123456789):",
        "track_enter_phone": "Введите *номер телефона* (например, +992XXXXXXXXX):",
        "search_none": "Ничего не найдено. Проверьте данные и попробуйте снова.",
        "search_again": "Ещё поиск? Выберите способ:",
        "about_text": (
            "🌏 **О нас — Yasroikard Logistic**\n\n"
            "🏢 **Адрес офиса:**\n"
            "Китай, провинция Чжэцзян, город Иу,\n"
            "улица ЦзянДун, район УАй Синь Цунь,\n"
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
            "🚚 **Сроки доставки**\n\n"
            "📍 **Таджикистан:** 18–26 дней\n"
            "📍 **Россия:** 13–18 дней\n"
            "📍 **Европа и США:** уточняйте у администратора\n\n"
            "💬 Для других стран свяжитесь с админом: @mg19981 или @Yasin_direct"
        ),
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
        "lang_pick": "Choose your language:",
        "lang_saved": "Language saved: {lang_name}",
        "channels_title": "Our channels:",
        "track_how": "How would you like to search?",
        "track_enter_code": "Enter *tracking code* (e.g., YA123456789):",
        "track_enter_phone": "Enter *phone number* (e.g., +1XXXXXXXXXX):",
        "search_none": "No results. Please check and try again.",
        "search_again": "Search again? Choose a method:",
        "about_text": "ℹ️ About us text (to be translated).",
        "delivery_text": "🚚 Delivery time info (to be translated).",
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
        "lang_pick": "Забонро интихоб кунед:",
        "lang_saved": "Забон нигоҳ дошта шуд: {lang_name}",
        "channels_title": "Каналҳои мо:",
        "track_how": "Чӣ тавр ҷустуҷӯ мекунед?",
        "track_enter_code": "Рамзи *трек*-ро ворид кунед:",
        "track_enter_phone": "Рақами *телефон*-ро ворид кунед:",
        "search_none": "Ёфт нашуд. Санҷед ва боз кӯшиш кунед.",
        "search_again": "Боз ҷустуҷӯ мекунед? Усулро интихоб кунед:",
        "about_text": "ℹ️ Дар бораи мо (ба зудӣ тарҷума мешавад).",
        "delivery_text": "🚚 Мӯҳлати расонӣ (ба зудӣ тарҷума мешавад).",
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
    txt = LANG.get(lang, LANG["ru"]).get(key, LANG["ru"].get(key, key))
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


# kewboard 

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
            InlineKeyboardButton(text=L["btn_lang"], callback_data="menu:lang"),
            InlineKeyboardButton(text=L["btn_admin"], callback_data="menu:admin"),
        ],
    ])

def channels_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Одежда", url="https://t.me/yasroikard_gr")],
        [InlineKeyboardButton(text="📱 Электроника", url="https://t.me/yasroikard_elektronika")],
        [InlineKeyboardButton(text="🕰 Часы и аксессуары", url="https://t.me/russiamanwatchs")],  # NEW
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")]
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

def track_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔢 По трек-коду", callback_data="track:by_code"),
            InlineKeyboardButton(text="📞 По телефону", callback_data="track:by_phone"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")]
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

def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:set:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:set:en"),
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang:set:tj"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")]
    ])

def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    # prefix examples: "ben:ordered", "ben:paid"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"{prefix}:yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"{prefix}:no"),
        ],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="ben:cancel")],
    ])

def benefit_menu_btn_kb() -> InlineKeyboardMarkup:
    # shown on success
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="menu:admin")],
    ])


# Calculator helpers
def calc_unit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Метры (м)", callback_data="calc:unit:m"),
            InlineKeyboardButton(text="Сантиметры (см)", callback_data="calc:unit:cm"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")],
    ])
def calc_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Новый расчёт", callback_data="menu:calc")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:back")],
    ])
def _parse_pos_float(s: str) -> float | None:
    try:
        s = s.replace(",", ".").strip()
        v = float(s)
        return v if v > 0 else None
    except:
        return None



# db helpers

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
    
async def save_benefit_row(admin_id: int, data: dict) -> tuple[bool, str]:
    """
    Expects data = {
      "whatsapp": str, "ordered": bool, "paid": bool,
      "real_cost": float, "user_paid": float
    }
    """
    try:
        benefit = float(data["real_cost"]) - float(data["user_paid"])
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


def format_benefit_row_line(r: dict) -> str:
    wa = r.get("whatsapp") or "—"
    paid = "Да" if r.get("paid") else "Нет"
    rc = f"{float(r.get('real_cost') or 0):.2f}"
    up = f"{float(r.get('user_paid') or 0):.2f}"
    bf = f"{float(r.get('benefit') or 0):.2f}"
    c  = (r.get("created_at") or "")[:19]
    return f"{wa} | Оплата: {paid} | Реал.: {rc} | Оплач.: {up} | Профит: {bf} | {c}"

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
    """
    Simple totals computed client-side.
    For large datasets consider a SQL view/edge function instead.
    """
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

    if total == 0:
        txt = (
            "📊 Учёт прибыли\n\n"
            "Пока записей нет.\n\n"
            f"ИТОГО: Реальная стоимость {rc_sum:.2f} | Оплачено {up_sum:.2f} | Прибыль {bf_sum:.2f}"
        )
        kb = ben_list_nav_kb(1, 1)
        return txt, kb

    total_pages = max(1, math.ceil(total / BEN_PAGE_SIZE))
    header = f"📊 Учёт прибыли — страница {page}/{total_pages}\nЗаписей: {total}\n"
    lines = [header, "```", "WhatsApp | Оплата | Реал. | Оплач. | Профит | Дата", "-" * 60]
    for r in rows:
        lines.append(format_benefit_row_line(r))
    lines.append("```")
    lines.append(f"ИТОГО: Реал. {rc_sum:.2f} | Оплач. {up_sum:.2f} | Профит {bf_sum:.2f}")
    text = "\n".join(lines)
    kb = ben_list_nav_kb(page, total_pages)
    return text, kb

async def show_admin_benefits(msg, admin_id: int, page: int):
    ADMIN_BEN_PAGE[admin_id] = page
    text, kb = await render_benefits_page(page)
    await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")


def format_ship_row_line(r: dict) -> str:
    t = r.get("tracking_code") or "—"
    s = r.get("status") or "—"
    p = r.get("phone") or "—"
    c = (r.get("created_at") or "")[:19]
    return f"{t} | {s} | {p} | {c}"

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


# calback

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

    if key == "channels":
        await cb.message.edit_text(t(uid, "channels_title"), reply_markup=channels_kb())
    elif key == "track":
        await cb.message.edit_text(t(uid, "track_how"), reply_markup=track_choice_kb())
    elif key == "calc":
        CALC_STATE[uid] = "calc_unit"; CALC_DATA[uid] = {}
        await cb.message.edit_text("📦 Расчёт объёма (м³).\nСначала выберите единицы измерения:", reply_markup=calc_unit_kb())
    elif key == "delivery":
        await cb.message.edit_text(LANG[get_lang(uid)]["delivery_text"], parse_mode="Markdown")
    elif key == "about":
        await cb.message.edit_text(LANG[get_lang(uid)]["about_text"], parse_mode="Markdown")
    elif key == "contact":
        await cb.message.edit_text("Контакты: @mg19981 • @Yasin_direct")
    elif key == "lang":
        await cb.message.edit_text(t(uid, "lang_pick"), reply_markup=lang_kb())
    elif key == "admin":
        if uid in ADMIN_IDS:
            await cb.message.edit_text("Админ-панель: выберите действие.", reply_markup=admin_menu_kb())
        else:
            await cb.message.edit_text("⛔ Доступ запрещён. Эта панель только для администраторов.")
    elif key == "req":
        USER_REQ_STATE[uid] = "req_track"; USER_REQ_DATA[uid] = {}
        await cb.message.edit_text("📥 Заявка на добавление отправления.\n\nВведите *трек-код*:", parse_mode="Markdown")
    elif key == "back":
        await cb.message.edit_text(t(uid, "menu_title"), reply_markup=main_menu_kb(get_lang(uid)))
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

# Admin: Benefit yes/no (ordered / paid)
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

# Admin: Benefit cancel
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
    ); await cb.answer()


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
    await cb.message.edit_text("Введите *высоту* в метрах (например, 1.2):", parse_mode="Markdown"); await cb.answer()

@dp.callback_query(F.data == "calc:unit:cm")
async def calc_unit_cm(cb: CallbackQuery):
    u = cb.from_user.id; CALC_STATE[u] = "calc_h"; CALC_DATA.setdefault(u, {})["unit"] = "cm"
    await cb.message.edit_text("Введите *высоту* в сантиметрах (например, 120):", parse_mode="Markdown"); await cb.answer()

# Admin: search shortcut
@dp.callback_query(F.data == "admin:search")
async def admin_search_start(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True); return
    await cb.message.edit_text("Как искать отправление?", reply_markup=track_choice_kb()); await cb.answer()

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



# message router


# === Part 5: message router + runner ===
@dp.message()
async def message_router(message: Message):
    user_id = message.from_user.id
    state = ADMIN_FLOW_STATE.get(user_id)

    # Admin add shipment — step 1 tracking
    if user_id in ADMIN_IDS and state == "awaiting_tracking":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий. Введите снова:"); return
        ADMIN_NEW_SHIPMENT[user_id]["tracking_code"] = tracking
        ADMIN_FLOW_STATE[user_id] = "awaiting_phone"
        await message.answer("📞 Введите *номер телефона* клиента (например, +992XXXXXXXXX):", parse_mode="Markdown"); return

    # Admin add shipment — step 2 phone
    if user_id in ADMIN_IDS and state == "awaiting_phone":
        phone_raw = (message.text or "").strip()
        phone = normalize_phone(phone_raw)
        if not PHONE_RE.match(phone):
            await message.answer("Неверный формат телефона. Пример: +992XXXXXXXXX. Введите снова:"); return
        ADMIN_NEW_SHIPMENT[user_id]["phone"] = phone
        ADMIN_FLOW_STATE[user_id] = "awaiting_description"
        await message.answer("📝 Введите *краткое описание* (например, «Электроника, 2 кг»):", parse_mode="Markdown"); return

    # Admin add shipment — step 3 description -> save
    if user_id in ADMIN_IDS and state == "awaiting_description":
        desc = (message.text or "").strip()
        if len(desc) < 3:
            await message.answer("Описание слишком короткое. Введите снова:"); return
        ADMIN_NEW_SHIPMENT[user_id]["description"] = desc
        ok, msg = await save_shipment_to_db(ADMIN_NEW_SHIPMENT[user_id])
        ADMIN_FLOW_STATE[user_id] = None; ADMIN_NEW_SHIPMENT[user_id] = {}
        await message.answer(msg); await message.answer("Админ-панель:", reply_markup=admin_menu_kb()); return

    # Admin change status — ask tracking
    if user_id in ADMIN_IDS and ADMIN_STATUS_STATE.get(user_id) == "awaiting_status_tracking":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий. Введите снова:"); return
        try:
            res = supabase_admin.table("shipments").select("id, tracking_code, status").eq("tracking_code", tracking).limit(1).execute()
            if not res.data:
                await message.answer("❗ Отправление с таким трек-кодом не найдено. Введите другой:"); return
        except Exception as e:
            await message.answer(f"Ошибка поиска отправления: {e}"); return
        ADMIN_STATUS_TARGET[user_id] = tracking; ADMIN_STATUS_STATE[user_id] = None
        await message.answer(f"Отправление найдено: *{tracking}*\nТекущий статус: {res.data[0].get('status') or '—'}\n\nВыберите новый статус:", parse_mode="Markdown", reply_markup=status_choice_kb()); return

    # USER REQUEST FLOW
    req_state = USER_REQ_STATE.get(user_id)
    if req_state == "req_track":
        tracking = (message.text or "").strip()
        if not tracking or len(tracking) < 5:
            await message.answer("Трек-код слишком короткий. Введите снова:"); return
        USER_REQ_DATA.setdefault(user_id, {})["tracking_code"] = tracking
        USER_REQ_STATE[user_id] = "req_phone_code"
        await message.answer("Выберите код страны для телефона:", reply_markup=phone_code_kb()); return

    if req_state == "req_phone_code_custom":
        code = (message.text or "").strip()
        if not code.startswith("+") or not re.sub(r"\D", "", code):
            await message.answer("Неверный код. Пример: +49. Введите ещё раз:"); return
        USER_REQ_DATA.setdefault(user_id, {})["phone_code"] = code
        USER_REQ_STATE[user_id] = "req_phone_local"
        await message.answer(f"Код выбран: {code}\nТеперь введите номер (без кода), только цифры:"); return

    if req_state == "req_phone_local":
        local = (message.text or "").strip().replace(" ", "").replace("-", "")
        code = USER_REQ_DATA[user_id].get("phone_code", "")
        full = normalize_phone(code + local)
        if not PHONE_RE.match(full):
            await message.answer("Неверный телефон. Введите только цифры после кода страны:"); return
        USER_REQ_DATA[user_id]["phone_local"] = local
        USER_REQ_DATA[user_id]["phone"] = full
        USER_REQ_STATE[user_id] = "req_country"
        await message.answer("Выберите страну:", reply_markup=country_kb()); return

    if req_state == "req_country_custom":
        country = (message.text or "").strip()
        if len(country) < 2:
            await message.answer("Слишком короткое название. Введите ещё раз:"); return
        USER_REQ_DATA[user_id]["country"] = country
        data = USER_REQ_DATA[user_id]
        try:
            supabase_admin.table("shipment_requests").insert({
                "user_id": user_id, "tracking_code": data["tracking_code"],
                "phone": data["phone"], "country": data["country"],
            }).execute()
        except Exception as e:
            await message.answer(f"Ошибка сохранения заявки: {e}")
            USER_REQ_STATE[user_id] = None; USER_REQ_DATA[user_id] = {}; return
        USER_REQ_STATE[user_id] = None; USER_REQ_DATA[user_id] = {}
        await message.answer("✅ Заявка отправлена на проверку администратору. Мы уведомим вас после подтверждения.")
        await message.answer(t(user_id, "menu_title"), reply_markup=main_menu_kb(get_lang(user_id))); return

    # Calculator flow (H -> W -> L)
    if CALC_STATE.get(user_id) == "calc_h":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = "м" if CALC_DATA.get(user_id, {}).get("unit") == "m" else "см"
            await message.answer(f"Неверное значение. Введите высоту в {unit}:"); return
        CALC_DATA[user_id]["h"] = v; CALC_STATE[user_id] = "calc_w"
        unit_phrase = "метрах" if CALC_DATA[user_id]["unit"] == "m" else "сантиметрах"
        await message.answer(f"Ок. Теперь введите *ширину* в {unit_phrase}:", parse_mode="Markdown"); return

    if CALC_STATE.get(user_id) == "calc_w":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = "м" if CALC_DATA.get(user_id, {}).get("unit") == "m" else "см"
            await message.answer(f"Неверное значение. Введите ширину в {unit}:"); return
        CALC_DATA[user_id]["w"] = v; CALC_STATE[user_id] = "calc_l"
        unit_phrase = "метрах" if CALC_DATA[user_id]["unit"] == "m" else "сантиметрах"
        await message.answer(f"Отлично. Теперь введите *длину* в {unit_phrase}:", parse_mode="Markdown"); return

    if CALC_STATE.get(user_id) == "calc_l":
        v = _parse_pos_float(message.text or "")
        if v is None:
            unit = "м" if CALC_DATA.get(user_id, {}).get("unit") == "m" else "см"
            await message.answer(f"Неверное значение. Введите длину в {unit}:"); return
        CALC_DATA[user_id]["l"] = v
        unit = CALC_DATA[user_id]["unit"]
        h, w, l = CALC_DATA[user_id]["h"], CALC_DATA[user_id]["w"], CALC_DATA[user_id]["l"]
        if unit == "cm":
            h, w, l = h/100.0, w/100.0, l/100.0
        volume_m3 = h * w * l
        CALC_STATE[user_id] = None; CALC_DATA[user_id] = {}
        await message.answer(f"📦 Объём: *{volume_m3:.3f} м³*", parse_mode="Markdown", reply_markup=calc_again_kb()); return


        # ---- Admin: BENEFIT FLOW (messages) ----
    if user_id in ADMIN_IDS and BEN_STATE.get(user_id) == "whatsapp":
        wa = (message.text or "").strip()
        # very lenient check: must have digits, optionally starts with +; you can harden this later
        if not re.search(r"\d", wa):
            await message.answer("Неверный формат WhatsApp. Введите ещё раз:")
            return
        BEN_DATA.setdefault(user_id, {})["whatsapp"] = wa
        BEN_STATE[user_id] = "ordered"
        await message.answer("Покупатель оформил заказ?\nВыберите вариант:", reply_markup=yes_no_kb("ben:ordered"))
        return

    if user_id in ADMIN_IDS and BEN_STATE.get(user_id) == "real_cost":
        val = _parse_pos_float(message.text or "")
        if val is None:
            await message.answer("Введите корректное число (реальная стоимость):")
            return
        BEN_DATA.setdefault(user_id, {})["real_cost"] = float(val)
        BEN_STATE[user_id] = "user_paid"
        await message.answer("Введите сумму, которую оплатил покупатель (число):")
        return

    if user_id in ADMIN_IDS and BEN_STATE.get(user_id) == "user_paid":
        val = _parse_pos_float(message.text or "")
        if val is None:
            await message.answer("Введите корректное число (оплачено покупателем):")
            return
        BEN_DATA.setdefault(user_id, {})["user_paid"] = float(val)

        # compute & save
        ok, msg = await save_benefit_row(user_id, BEN_DATA[user_id])
        # Show summary
        d = BEN_DATA[user_id]
        benefit = d["real_cost"] - d["user_paid"]
        summary = (
            "💹 **Итог по сделке**\n\n"
            f"WhatsApp: {d['whatsapp']}\n"
            f"Заказ оформлен: {'Да' if d['ordered'] else 'Нет'}\n"
            f"Оплата получена: {'Да' if d['paid'] else 'Нет'}\n"
            f"Реальная стоимость: {d['real_cost']:.2f}\n"
            f"Оплачено клиентом: {d['user_paid']:.2f}\n"
            f"**Прибыль:** {benefit:.2f}\n\n"
            + msg
        )
        # reset
        BEN_STATE[user_id] = None
        BEN_DATA[user_id] = {}

        await message.answer(summary, parse_mode="Markdown", reply_markup=benefit_menu_btn_kb())
        return



    # User (or admin) search flow
    if USER_TRACK_STATE.get(user_id):
        query = (message.text or "").strip()
        if not query:
            await message.answer("Пустой запрос. Введите значение:"); return
        mode = USER_TRACK_MODE.get(user_id)
        results = await find_shipments(query, mode)
        USER_TRACK_STATE[user_id] = False; USER_TRACK_MODE[user_id] = ""
        if not results:
            await message.answer(t(user_id, "search_none"))
            await message.answer(t(user_id, "search_again"), reply_markup=track_choice_kb()); return
        if mode == "code":
            await message.answer("Найдено отправление:\n\n" + format_shipment_row(results[0]))
            await message.answer(t(user_id, "search_again"), reply_markup=track_choice_kb()); return
        if mode == "phone":
            header = f"Найдено отправлений по номеру {normalize_phone(query)}: {len(results)}"
            chunks, sep = [header], "\n" + ("—" * 24) + "\n"
            for r in results:
                chunks.append(format_shipment_row(r))
            await message.answer(sep.join(chunks))
            await message.answer(t(user_id, "search_again"), reply_markup=track_choice_kb()); return
        if len(results) == 1:
            await message.answer("Найдено отправление:\n\n" + format_shipment_row(results[0]))
        else:
            header = f"Найдено отправлений: {len(results)}"
            chunks, sep = [header], "\n" + ("—" * 24) + "\n"
            for r in results:
                chunks.append(format_shipment_row(r))
            await message.answer(sep.join(chunks))
        await message.answer(t(user_id, "search_again"), reply_markup=track_choice_kb()); return

# Request flow button handlers (custom code & country)
@dp.callback_query(F.data.startswith("req:code:"))
async def req_choose_code(cb: CallbackQuery):
    u = cb.from_user.id
    if USER_REQ_STATE.get(u) != "req_phone_code": await cb.answer(); return
    _, _, code = cb.data.partition("req:code:")
    if code == "custom":
        USER_REQ_DATA.setdefault(u, {})["phone_code"] = ""
        USER_REQ_STATE[u] = "req_phone_code_custom"
        await cb.message.edit_text("Введите код страны вручную (например, +49):"); await cb.answer(); return
    USER_REQ_DATA.setdefault(u, {})["phone_code"] = code
    USER_REQ_STATE[u] = "req_phone_local"
    await cb.message.edit_text(f"Код выбран: {code}\nТеперь введите номер (без кода), только цифры:"); await cb.answer()

@dp.callback_query(F.data.startswith("req:country:"))
async def req_choose_country(cb: CallbackQuery):
    u = cb.from_user.id
    if USER_REQ_STATE.get(u) != "req_country": await cb.answer(); return
    _, _, country = cb.data.partition("req:country:")
    if country == "custom":
        USER_REQ_STATE[u] = "req_country_custom"
        await cb.message.edit_text("Введите название страны вручную:"); await cb.answer(); return
    USER_REQ_DATA.setdefault(u, {})["country"] = country
    data = USER_REQ_DATA[u]
    try:
        supabase_admin.table("shipment_requests").insert({
            "user_id": u, "tracking_code": data["tracking_code"],
            "phone": normalize_phone(data["phone"]), "country": country,
        }).execute()
    except Exception as e:
        await cb.message.edit_text(f"Ошибка сохранения заявки: {e}")
        USER_REQ_STATE[u] = None; USER_REQ_DATA[u] = {}; await cb.answer(); return
    USER_REQ_STATE[u] = None; USER_REQ_DATA[u] = {}
    await cb.message.edit_text("✅ Заявка отправлена на проверку администратору. Мы уведомим вас после подтверждения.")
    await cb.message.answer(t(u, "menu_title"), reply_markup=main_menu_kb(get_lang(u))); await cb.answer()

# Runner
async def main():
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
