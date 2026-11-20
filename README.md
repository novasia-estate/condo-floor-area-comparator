# Condo Floor Area Comparator

A two-offer Streamlit worksheet for comparing asking prices on a common enclosed-area basis. The examples use invented quotes. Enter each quote’s actual area boundary, compare a range if measurements are uncertain, and download the current comparison.

Run `pip install -r requirements.txt` followed by `streamlit run app.py`. The area calculations in floor_area.py are pure Python. The app stores its current input in session state and collects no contact information.

The tool distinguishes enclosed area, the rough planning remainder after stated storage and circulation, and price per enclosed square metre. Use a dimensioned plan to check whether exterior space or common allocations are counted. [Buyer evidence guide](https://novasia.estate/en/cambodia/unit-selection-checklist/).
