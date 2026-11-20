"""Buyer-facing Streamlit app for analysing two quotes on the same area basis."""

import csv
from io import StringIO

import streamlit as st

from floor_area import FloorQuote, compare_area, ranking


SOURCE = "https://novasia.estate/en/cambodia/unit-selection-checklist/"
DEMO = {
    "A": (130_000, 60.0, 100, True, 3.0, 12.0, 2.4, 6.0),
    "B": (126_000, 47.0, 100, False, 4.0, 0.0, 3.2, 4.0),
}


def format_range(interval, places=1):
    low, high = interval
    return f"{low:,.{places}f}" if abs(low - high) < 1e-8 else f"{low:,.{places}f}–{high:,.{places}f}"


def component(label, initial, uncertain, key):
    first = st.number_input(label if not uncertain else f"{label}, lower bound",
                            min_value=0.0, value=initial, step=0.1, key=f"{key}_lo")
    if not uncertain:
        return first, first
    second = st.number_input(f"{label}, upper bound", min_value=0.0,
                             value=initial + 2.0, step=0.1, key=f"{key}_hi")
    return first, second


def offer(key, mode):
    suffix = f"{key}_{mode}"
    defaults = DEMO[key] if mode == "Worked example" else (0, 0.0, 0, False, 0.0, 0.0, 0.0, 0.0)
    price, size, percentage, share, balcony, common, storage, circulation = defaults
    st.subheader(f"Offer {key}")
    ask = st.number_input("Asking price, USD", min_value=0, value=price, step=1_000, key=f"price_{suffix}")
    quoted = st.number_input("Area printed on the quote, m²", min_value=0.0, value=size,
                             step=0.1, key=f"quote_{suffix}")
    with st.expander("Set the area boundary", expanded=True):
        portion = st.select_slider("Balcony share counted in the quoted area",
                                   [0, 25, 50, 75, 100], value=percentage, format_func=lambda n: f"{n}%",
                                   key=f"balcony_portion_{suffix}")
        includes_common = st.checkbox("The area includes an allocated common share",
                                       value=share, key=f"common_switch_{suffix}")
        uncertain = st.checkbox("Compare a measured range", key=f"range_{suffix}")
        balcony_bounds = component("Physical balcony, m²", balcony, uncertain, f"balcony_{suffix}") if portion else (0, 0)
        common_bounds = component("Common share included, m²", common, uncertain, f"common_{suffix}") if includes_common else (0, 0)
        store = st.number_input("Enclosed storage already in the plan, m²", min_value=0.0, value=storage,
                                step=0.1, key=f"store_{suffix}")
        movement = st.number_input("Enclosed circulation already in the plan, m²", min_value=0.0, value=circulation,
                                   step=0.1, key=f"movement_{suffix}")
    documented = mode == "Worked example" or st.checkbox(
        "I have a stated area boundary or entered an explicit range", key=f"basis_{suffix}"
    )
    return FloorQuote(ask, quoted, portion / 100, includes_common, balcony_bounds, common_bounds, store, movement), documented


st.set_page_config(page_title="Condo Floor Area Comparator", page_icon="📐", layout="wide")
st.title("Condo Floor Area Comparator")
st.write("Put two quotes on the same enclosed-area basis before comparing price. Separate any balcony or common share that the quote includes.")
mode = st.radio("Start with", ["Worked example", "My own quotes"], horizontal=True)
if mode == "Worked example":
    st.caption("The default offers are fictional. Offer A starts at 60 m² and includes a common share. Offer B starts at 47 m² and includes a private balcony.")

cols = st.columns(2)
quotes = {}
for name, col in zip(("A", "B"), cols):
    with col:
        quotes[name] = offer(name, mode)

results = {}
for name, (quote, documented) in quotes.items():
    if mode == "My own quotes" and (quote.ask == 0 or quote.quoted == 0):
        st.info(f"Enter the price and quoted size for Offer {name} to calculate it.")
        continue
    if not documented:
        st.info(f"Offer {name} needs a documented area boundary or an explicit scenario before comparison.")
        continue
    try:
        results[name] = compare_area(quote)
    except ValueError as err:
        st.error(f"Offer {name}. {err}")

if results:
    st.subheader("Compare on the same basis")
    rows = []
    for name, result in results.items():
        rows.append({"Offer": name, "Enclosed area, m²": format_range(result.enclosed_m2),
                     "Enclosed less storage and circulation, m²": format_range(result.room_remainder_m2),
                     "USD per enclosed m²": format_range(result.ask_per_enclosed_m2, 0)})
    st.table(rows)
    if len(results) == 2:
        st.info(ranking(results["A"].enclosed_m2, results["B"].enclosed_m2))
    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    st.download_button("Download this comparison (CSV)", out.getvalue(), "condo-area-comparison.csv", "text/csv")

with st.expander("How to read the numbers"):
    st.markdown(
        "Enclosed area = quoted area − included balcony weight × physical balcony − allocated common share already in the quote. "
        "The second column removes only the storage and circulation amounts you entered. It is a planning remainder and can still include kitchens and bathrooms. "
        "No adjustment is inferred for walls, balconies or common space when the quoted definition is unknown. Ask for a dimensioned plan before entering an assumed boundary. "
        "The price range uses the inverse of the area range. The model compares asking prices in one currency and does not calculate tax or fees."
    )

st.markdown(f"Prepared by **NovAsia Estate** · [Questions to ask about the exact unit and its area]({SOURCE})")
