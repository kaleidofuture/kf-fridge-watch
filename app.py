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
from datetime import date, datetime

import pendulum
import humanize

# --- Header ---
render_header()

# --- Session state initialization ---
if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = []


def get_days_remaining(expiry_str: str) -> int:
    """Calculate days remaining until expiry."""
    expiry = pendulum.parse(expiry_str, tz=None)
    today = pendulum.today()
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


# --- Add new item ---
st.subheader(t("add_item_title"))

item_name = st.text_input(t("item_name"), placeholder=t("item_name_placeholder"))
purchase_date = st.date_input(t("purchase_date"), value=date.today())
expiry_date = st.date_input(t("expiry_date"), value=None)

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

        st.markdown(
            f'<div style="background:{bg_color}; border:1px solid {border_color}; '
            f'border-radius:8px; padding:12px; margin-bottom:8px;">'
            f'<div style="font-size:1.1rem; font-weight:bold;">{emoji} {item["name"]}</div>'
            f'<div style="color:#666; font-size:0.85rem; margin-top:4px;">'
            f'{t("purchased")}: {item["purchase_date"]}</div>'
            f'<div style="font-weight:bold; margin-top:4px;">{remaining}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("\U0001F5D1", key=f"del_{idx}"):
            items_to_delete.append(idx)

    if items_to_delete:
        for idx in sorted(items_to_delete, reverse=True):
            st.session_state.fridge_items.pop(idx)
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

            st.success(t("import_success").format(count=len(imported)))
            st.rerun()
        except Exception as e:
            st.error(t("import_error").format(error=str(e)))

    # Clear all
    if st.button(t("clear_all"), type="secondary"):
        st.session_state.fridge_items = []
        st.rerun()

else:
    st.info(t("no_items"))

# --- Footer ---
render_footer(libraries=["Pendulum", "Humanize"])
