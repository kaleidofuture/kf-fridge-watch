"""KF-FridgeWatch — Track food expiry dates and reduce waste."""

import streamlit as st

st.set_page_config(
    page_title="KF-FridgeWatch",
    page_icon="\U0001F9CA",
    layout="centered",
)

from components.header import render_header
from components.footer import render_footer
from components.i18n import t

import json
import csv
import io
from datetime import date, datetime, timedelta

import pendulum
import humanize
from streamlit_js_eval import streamlit_js_eval

STORAGE_KEY = "kf-fridge-watch-items"

# --- Food Database ---
FOOD_DB = {
    # 卵・乳製品
    "卵": {"category": "卵・乳製品", "default_days": 14, "freezable": False, "freeze_tip": ""},
    "牛乳": {"category": "卵・乳製品", "default_days": 7, "freezable": True, "freeze_tip": "製氷皿で凍らせて料理用に（1ヶ月）"},
    "ヨーグルト": {"category": "卵・乳製品", "default_days": 10, "freezable": True, "freeze_tip": "小分けにして冷凍OK（1ヶ月）"},
    "バター": {"category": "卵・乳製品", "default_days": 30, "freezable": True, "freeze_tip": "小分けラップで冷凍OK（1ヶ月）"},
    "チーズ": {"category": "卵・乳製品", "default_days": 14, "freezable": True, "freeze_tip": "シュレッドチーズはそのまま冷凍OK（1ヶ月）"},
    # 肉類
    "豚肉": {"category": "肉類", "default_days": 3, "freezable": True, "freeze_tip": "小分けラップ→保存袋で冷凍OK（1ヶ月）"},
    "鶏肉": {"category": "肉類", "default_days": 2, "freezable": True, "freeze_tip": "下味冷凍がおすすめ（1ヶ月）"},
    "ハム": {"category": "肉類", "default_days": 7, "freezable": True, "freeze_tip": "1枚ずつラップで冷凍OK（1ヶ月）"},
    "ベーコン": {"category": "肉類", "default_days": 7, "freezable": True, "freeze_tip": "小分けラップで冷凍OK（1ヶ月）"},
    # 野菜
    "キャベツ": {"category": "野菜", "default_days": 7, "freezable": True, "freeze_tip": "ざく切りで生のまま冷凍OK（1ヶ月）"},
    "にんじん": {"category": "野菜", "default_days": 14, "freezable": True, "freeze_tip": "薄切り・短冊切りで冷凍OK（1ヶ月）"},
    "たまねぎ": {"category": "野菜", "default_days": 30, "freezable": True, "freeze_tip": "みじん切りで冷凍→時短に（1ヶ月）"},
    "じゃがいも": {"category": "野菜", "default_days": 30, "freezable": True, "freeze_tip": "マッシュにして冷凍OK（1ヶ月）"},
    "トマト": {"category": "野菜", "default_days": 7, "freezable": True, "freeze_tip": "丸ごと冷凍→凍ったまますりおろしてソースに（1ヶ月）"},
    "きゅうり": {"category": "野菜", "default_days": 5, "freezable": True, "freeze_tip": "薄切り＋塩もみして冷凍OK（2週間）"},
    "レタス": {"category": "野菜", "default_days": 5, "freezable": False, "freeze_tip": ""},
    "もやし": {"category": "野菜", "default_days": 2, "freezable": True, "freeze_tip": "袋のまま冷凍OK（2週間）"},
    # 豆腐・大豆製品
    "豆腐": {"category": "大豆製品", "default_days": 5, "freezable": True, "freeze_tip": "水切り後冷凍→高野豆腐風に（1ヶ月）"},
    "納豆": {"category": "大豆製品", "default_days": 7, "freezable": True, "freeze_tip": "パックのまま冷凍OK（1ヶ月）"},
    # パン
    "食パン": {"category": "パン", "default_days": 4, "freezable": True, "freeze_tip": "1枚ずつラップ→保存袋で冷凍OK（1ヶ月）"},
    # --- Additional items for DB lookup (not in quick-add grid) ---
    "ごぼう": {"category": "野菜", "default_days": 7, "freezable": True, "freeze_tip": "茹でて冷凍OK（1ヶ月）"},
    "ほうれん草": {"category": "野菜", "default_days": 3, "freezable": True, "freeze_tip": "茹でて水気を絞り冷凍OK（1ヶ月）"},
    "ブロッコリー": {"category": "野菜", "default_days": 5, "freezable": True, "freeze_tip": "小房に分けて茹で冷凍OK（1ヶ月）"},
    "大根": {"category": "野菜", "default_days": 10, "freezable": True, "freeze_tip": "カット→生のまま冷凍OK（1ヶ月）"},
    "ねぎ": {"category": "野菜", "default_days": 7, "freezable": True, "freeze_tip": "小口切りで冷凍OK（1ヶ月）"},
    "しめじ": {"category": "きのこ", "default_days": 5, "freezable": True, "freeze_tip": "ほぐして保存袋で冷凍OK（1ヶ月）"},
    "えのき": {"category": "きのこ", "default_days": 5, "freezable": True, "freeze_tip": "ほぐして保存袋で冷凍OK（1ヶ月）"},
    "豚ひき肉": {"category": "肉類", "default_days": 2, "freezable": True, "freeze_tip": "薄く平らにして冷凍OK（1ヶ月）"},
    "鶏ひき肉": {"category": "肉類", "default_days": 2, "freezable": True, "freeze_tip": "薄く平らにして冷凍OK（1ヶ月）"},
    "牛肉": {"category": "肉類", "default_days": 3, "freezable": True, "freeze_tip": "小分けラップ→保存袋で冷凍OK（1ヶ月）"},
    "鮭": {"category": "魚介類", "default_days": 2, "freezable": True, "freeze_tip": "1切れずつラップで冷凍OK（2週間）"},
    "ウインナー": {"category": "肉類", "default_days": 14, "freezable": True, "freeze_tip": "袋のまま冷凍OK（1ヶ月）"},
}

# Quick-add items (20 common foods)
QUICK_ADD_ITEMS = [
    "卵", "牛乳", "キャベツ", "にんじん", "豚肉",
    "鶏肉", "豆腐", "もやし", "たまねぎ", "じゃがいも",
    "トマト", "きゅうり", "レタス", "納豆", "ヨーグルト",
    "バター", "チーズ", "ハム", "ベーコン", "食パン",
]

QUICK_ADD_EMOJIS = {
    "卵": "\U0001F95A", "牛乳": "\U0001F95B", "キャベツ": "\U0001F966",
    "にんじん": "\U0001F955", "豚肉": "\U0001F969", "鶏肉": "\U0001F357",
    "豆腐": "\U0001FAD8", "もやし": "\U0001F331", "たまねぎ": "\U0001F9C5",
    "じゃがいも": "\U0001F954", "トマト": "\U0001F345", "きゅうり": "\U0001F952",
    "レタス": "\U0001F96C", "納豆": "\U0001FAD8", "ヨーグルト": "\U0001F95B",
    "バター": "\U0001F9C8", "チーズ": "\U0001F9C0", "ハム": "\U0001F356",
    "ベーコン": "\U0001F953", "食パン": "\U0001F35E",
}

# --- Header ---
render_header()

# --- Session state initialization ---
if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = []

# --- Load from localStorage ---
if "data_loaded" not in st.session_state:
    stored = streamlit_js_eval(js_expressions=f'localStorage.getItem("{STORAGE_KEY}")')
    if stored and stored != "null":
        try:
            st.session_state.fridge_items = json.loads(stored)
        except Exception:
            pass
    st.session_state.data_loaded = True


def save_to_local_storage():
    """Save fridge_items to browser localStorage."""
    data_json = json.dumps(st.session_state.fridge_items, ensure_ascii=False)
    streamlit_js_eval(js_expressions=f'localStorage.setItem("{STORAGE_KEY}", {json.dumps(data_json)})')


def get_days_remaining(expiry_str: str) -> int:
    """Calculate days remaining until expiry."""
    from datetime import date as _date
    expiry = _date.fromisoformat(str(expiry_str)[:10])
    today = _date.today()
    return (expiry - today).days


def format_remaining(days: int, lang: str) -> str:
    """Format remaining days in a human-friendly way."""
    if lang == "ja":
        if days < 0:
            return f"{abs(days)}日前に期限切れ"
        elif days == 0:
            return "今日が期限"
        elif days == 1:
            return "あと1日"
        else:
            return f"あと{days}日"
    else:
        if days < 0:
            return f"Expired {abs(days)} days ago"
        elif days == 0:
            return "Expires today"
        elif days == 1:
            return "1 day left"
        else:
            return f"{days} days left"


def get_status_emoji(days: int) -> str:
    """Return status emoji based on days remaining."""
    if days < 0:
        return "\U0001F6A8"
    elif days <= 1:
        return "\U0001F534"
    elif days <= 3:
        return "\U0001F7E0"
    elif days <= 7:
        return "\U0001F7E1"
    else:
        return "\U0001F7E2"


def lookup_food_db(name: str) -> dict | None:
    """Look up a food item in the database. Returns entry or None."""
    if name in FOOD_DB:
        return FOOD_DB[name]
    # Partial match fallback
    for key, val in FOOD_DB.items():
        if key in name or name in key:
            return val
    return None


def get_default_expiry(name: str) -> date:
    """Get default expiry date based on food DB, or 7 days fallback."""
    entry = lookup_food_db(name)
    days = entry["default_days"] if entry else 7
    return date.today() + timedelta(days=days)


def add_item_to_fridge(name: str, expiry: date | None = None):
    """Add an item to the fridge with auto-expiry from DB."""
    if expiry is None:
        expiry = get_default_expiry(name)
    st.session_state.fridge_items.append({
        "name": name,
        "purchase_date": str(date.today()),
        "expiry_date": str(expiry),
    })


# --- Quick Add Section ---
st.subheader(t("quick_add_title"))
st.caption(t("quick_add_description"))

# Display as a 5-column grid, 4 rows
cols_per_row = 5
for row_start in range(0, len(QUICK_ADD_ITEMS), cols_per_row):
    cols = st.columns(cols_per_row)
    for col_idx, col in enumerate(cols):
        item_idx = row_start + col_idx
        if item_idx < len(QUICK_ADD_ITEMS):
            item_name = QUICK_ADD_ITEMS[item_idx]
            emoji = QUICK_ADD_EMOJIS.get(item_name, "")
            with col:
                if st.button(f"{emoji}\n{item_name}", key=f"quick_{item_name}", use_container_width=True):
                    add_item_to_fridge(item_name)
                    save_to_local_storage()
                    st.success(t("item_added").format(name=item_name))
                    st.rerun()

st.markdown("---")

# --- Add new item (manual) ---
st.subheader(t("add_item_title"))

item_name = st.text_input(t("item_name"), placeholder=t("item_name_placeholder"))

# Auto-fill expiry from DB when item name is entered
default_expiry = None
db_entry = None
if item_name.strip():
    db_entry = lookup_food_db(item_name.strip())
    if db_entry:
        default_expiry = date.today() + timedelta(days=db_entry["default_days"])
        st.caption(t("auto_expiry_hint").format(days=db_entry["default_days"], category=db_entry["category"]))

purchase_date = st.date_input(t("purchase_date"), value=date.today())
expiry_date = st.date_input(t("expiry_date"), value=default_expiry)

if st.button(t("add_button"), type="primary"):
    if not item_name.strip():
        st.warning(t("no_item_name"))
    elif expiry_date is None:
        st.warning(t("no_expiry"))
    else:
        st.session_state.fridge_items.append({
            "name": item_name.strip(),
            "purchase_date": str(purchase_date),
            "expiry_date": str(expiry_date),
        })
        save_to_local_storage()
        st.success(t("item_added").format(name=item_name.strip()))
        st.rerun()

# --- Display items ---
if st.session_state.fridge_items:
    st.subheader(t("your_items_title"))

    lang = st.session_state.get("lang", "ja")

    # Sort by expiry date
    sorted_items = sorted(
        enumerate(st.session_state.fridge_items),
        key=lambda x: x[1]["expiry_date"],
    )

    # Summary stats
    expired_count = sum(1 for _, item in sorted_items if get_days_remaining(item["expiry_date"]) < 0)
    urgent_count = sum(1 for _, item in sorted_items if 0 <= get_days_remaining(item["expiry_date"]) <= 3)

    if expired_count > 0:
        st.error(t("expired_count").format(count=expired_count))
    if urgent_count > 0:
        st.warning(t("urgent_count").format(count=urgent_count))

    # Display each item
    items_to_delete = []
    for idx, item in sorted_items:
        days = get_days_remaining(item["expiry_date"])
        emoji = get_status_emoji(days)
        remaining = format_remaining(days, lang)

        if days < 0:
            bg_color = "#FFE0E0"
            border_color = "#FF8A8A"
        elif days <= 3:
            bg_color = "#FFF3E0"
            border_color = "#FFB74D"
        else:
            bg_color = "#F0F0F0"
            border_color = "#E0E0E0"

        # Build freeze tip HTML if expiry <= 2 days and freezable
        freeze_tip_html = ""
        if days <= 2:
            db_info = lookup_food_db(item["name"])
            if db_info and db_info["freezable"] and db_info["freeze_tip"]:
                freeze_tip_html = (
                    f'<div style="background:#E3F2FD; border-radius:4px; padding:6px 8px; '
                    f'margin-top:6px; font-size:0.85rem;">'
                    f'\U0001F9CA {t("freeze_tip_label")}: {item["name"]}\u2192{db_info["freeze_tip"]}'
                    f'</div>'
                )

        # Build recipe link HTML if expiry <= 3 days
        recipe_html = ""
        if days <= 3:
            import urllib.parse
            search_query = urllib.parse.quote(item["name"])
            recipe_url = f"https://www.kurashiru.com/search?query={search_query}"
            recipe_html = (
                f'<div style="margin-top:6px;">'
                f'<a href="{recipe_url}" target="_blank" style="color:#E16B5A; text-decoration:none; font-size:0.85rem;">'
                f'\U0001F373 {t("recipe_link_label")}'
                f'</a></div>'
            )

        st.markdown(
            f'<div style="background:{bg_color}; border:1px solid {border_color}; '
            f'border-radius:8px; padding:12px; margin-bottom:8px;">'
            f'<div style="font-size:1.1rem; font-weight:bold;">{emoji} {item["name"]}</div>'
            f'<div style="color:#666; font-size:0.85rem; margin-top:4px;">'
            f'{t("purchased")}: {item["purchase_date"]}</div>'
            f'<div style="font-weight:bold; margin-top:4px;">{remaining}</div>'
            f'{freeze_tip_html}'
            f'{recipe_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("\U0001F5D1", key=f"del_{idx}"):
            items_to_delete.append(idx)

    if items_to_delete:
        for idx in sorted(items_to_delete, reverse=True):
            st.session_state.fridge_items.pop(idx)
        save_to_local_storage()
        st.rerun()

    st.markdown("---")

    # --- Export/Import ---
    st.subheader(t("export_import_title"))

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        # CSV Export
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=["name", "purchase_date", "expiry_date"])
        writer.writeheader()
        for item in st.session_state.fridge_items:
            writer.writerow(item)
        st.download_button(
            label=t("export_csv"),
            data=csv_buffer.getvalue(),
            file_name="fridge_watch.csv",
            mime="text/csv",
        )

    with col_exp2:
        # JSON Export
        json_data = json.dumps(st.session_state.fridge_items, ensure_ascii=False, indent=2)
        st.download_button(
            label=t("export_json"),
            data=json_data,
            file_name="fridge_watch.json",
            mime="application/json",
        )

    # Import
    st.markdown(f"**{t('import_title')}**")
    uploaded = st.file_uploader(t("import_prompt"), type=["csv", "json"])
    if uploaded is not None:
        try:
            content = uploaded.read().decode("utf-8")
            if uploaded.name.endswith(".json"):
                imported = json.loads(content)
            else:
                reader = csv.DictReader(io.StringIO(content))
                imported = [row for row in reader]

            for item in imported:
                if "name" in item and "expiry_date" in item:
                    if "purchase_date" not in item:
                        item["purchase_date"] = str(date.today())
                    st.session_state.fridge_items.append({
                        "name": item["name"],
                        "purchase_date": item["purchase_date"],
                        "expiry_date": item["expiry_date"],
                    })

            save_to_local_storage()
            st.success(t("import_success").format(count=len(imported)))
            st.rerun()
        except Exception as e:
            st.error(t("import_error").format(error=str(e)))

    # Clear all
    if st.button(t("clear_all"), type="secondary"):
        st.session_state.fridge_items = []
        save_to_local_storage()
        st.rerun()

else:
    st.info(t("no_items"))

# --- Footer ---
render_footer(libraries=["Pendulum", "Humanize"], repo_name="kf-fridge-watch")
