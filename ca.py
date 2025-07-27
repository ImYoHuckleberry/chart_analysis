import streamlit as st
import pandas as pd
import plotly.graph_objs as go

@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    df['candle_idx'] = df.index
    return df

df = load_data()
max_idx = len(df) - 1

# Session state for trades and regions
if 'trades' not in st.session_state:
    st.session_state['trades'] = []
if 'selected_trade_idx' not in st.session_state:
    st.session_state['selected_trade_idx'] = None
if 'add_trade_mode' not in st.session_state:
    st.session_state['add_trade_mode'] = False
if 'add_region_mode' not in st.session_state:
    st.session_state['add_region_mode'] = False
if 'new_region_start' not in st.session_state:
    st.session_state['new_region_start'] = None
if 'new_region_end' not in st.session_state:
    st.session_state['new_region_end'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = "dark"

# THEME TOGGLE (SUN/MOON)
def sunmoon_switch():
    toggle = st.button("🌙" if st.session_state['theme'] == "dark" else "☀️", key="theme_toggle", help="Toggle theme")
    if toggle:
        st.session_state['theme'] = "light" if st.session_state['theme'] == "dark" else "dark"
        st.experimental_rerun()
sunmoon_switch()

# CSS Styling
st.markdown("""
<style>
body, .stApp { background-color: #171717 !important; color: #f5f5f5 !important; }
th { background: #232323 !important; color: #fafafa !important; font-size:14px; font-weight:600; border-bottom:1px solid #444;}
td { background: #232323 !important; color: #d3d3d3 !important; font-size:13px; font-weight:normal;}
.minimal-table td, .minimal-table th { text-align: center; padding: 6px 6px; border-bottom:1px solid #333;}
.minimal-table tr:last-child td { border-bottom:0;}
.plus-btn { font-size: 18px; color: #0af; font-weight: bold; cursor: pointer;}
tr.selected-row td { background: #1c305c !important; }
</style>
""", unsafe_allow_html=True)

# --- Trades Table ---
st.markdown("#### Trades")
st.markdown(
    "<div class='minimal-table'><table width='100%'><tr>"
    "<th>#</th><th>Name</th><th>Tag</th><th>Entry</th><th>Exit</th><th></th></tr>",
    unsafe_allow_html=True)
trades = st.session_state['trades']

if trades:
    for idx, trade in enumerate(trades):
        row_select = ""
        if st.session_state['selected_trade_idx'] == idx:
            row_select = "selected-row"
        st.markdown(
            f"<tr class='{row_select}'>"
            f"<td>{idx+1}</td>"
            f"<td>{trade['name']}</td>"
            f"<td>{trade['tag']}</td>"
            f"<td>{trade['entry']}</td>"
            f"<td>{trade['exit']}</td>"
            f"<td class='plus-btn'></td>"
            f"</tr>", unsafe_allow_html=True)
else:
    # Blank row for first trade
    st.markdown(
        "<tr><td></td><td></td><td></td><td></td><td></td>"
        "<td class='plus-btn'>+</td></tr>", unsafe_allow_html=True)

# Always show blank row with + for adding
if trades:
    st.markdown(
        "<tr><td></td><td></td><td></td><td></td><td></td>"
        "<td class='plus-btn'>+</td></tr>", unsafe_allow_html=True)
st.markdown("</table></div>", unsafe_allow_html=True)

# --- Trade Selection/Creation Logic ---
# (Streamlit limitation: no on-row click for HTML tables, so use selectbox for selection and button for add)
trade_names = [f"{i+1}: {t['name']}" for i, t in enumerate(trades)]
selected_trade = st.selectbox("Select Trade", ["Add New Trade"] + trade_names, key="trade_select")
if selected_trade == "Add New Trade":
    st.session_state['add_trade_mode'] = True
    st.session_state['selected_trade_idx'] = None
else:
    sel_idx = trade_names.index(selected_trade)
    st.session_state['selected_trade_idx'] = sel_idx
    st.session_state['add_trade_mode'] = False

# --- Trade Add/Edit Controls ---
if st.session_state['add_trade_mode']:
    with st.sidebar:
        st.markdown("#### New Trade")
        trade_name = st.text_input("Trade Name")
        tag = st.text_input("Tag")
        entry = st.text_input("Entry Date (YYYY-MM-DD)")
        exit = st.text_input("Exit Date (YYYY-MM-DD)")
        if st.button("Save Trade"):
            trades.append({
                "name": trade_name,
                "tag": tag,
                "entry": entry,
                "exit": exit,
                "regions": []
            })
            st.session_state['add_trade_mode'] = False
            st.experimental_rerun()
else:
    with st.sidebar:
        if st.session_state['selected_trade_idx'] is not None:
            trade = trades[st.session_state['selected_trade_idx']]
            st.markdown(f"#### Trade: {trade['name']}")
            # REGIONS TABLE
            st.markdown("##### Add/Edit Region")
            if st.session_state['add_region_mode']:
                # Chart click logic pseudo-code:
                st.info("Click two candles on the chart to define region (Streamlit-native click-to-candle not supported yet, use number inputs for demo).")
                start_idx = st.number_input("Start Candle", min_value=0, max_value=max_idx-1, value=10, step=1)
                end_idx = st.number_input("End Candle", min_value=start_idx+1, max_value=max_idx, value=20, step=1)
            else:
                start_idx, end_idx = 10, 20

            category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"])
            feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"])
            feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"])
            key_price = st.number_input("Key Price", value=float(df.loc[end_idx, 'close']), step=0.01, format="%.2f")
            tags = st.text_input("Region Tags")
            notes = st.text_area("Region Notes")

            if st.button("Add Region"):
                trade['regions'].append({
                    "Category": category,
                    "Feature 1": feature1,
                    "Feature 2": feature2,
                    "Start Date": df.loc[start_idx, 'time'][:10],
                    "Start Candle": start_idx,
                    "End Date": df.loc[end_idx, 'time'][:10],
                    "End Candle": end_idx,
                    "Key Price": key_price,
                    "Tags": tags,
                    "Notes": notes
                })
                st.experimental_rerun()

# --- Regions Table Below Chart ---
st.markdown("#### Regions (for selected trade)")
st.markdown(
    "<div class='minimal-table'><table width='100%'><tr>"
    "<th>#</th><th>Category</th><th>Feature 1</th><th>Feature 2</th><th>Start Date</th><th>Start Candle</th>"
    "<th>End Date</th><th>End Candle</th><th>Key Price</th><th>Tags</th><th>Notes</th><th></th></tr>",
    unsafe_allow_html=True)
regions = []
if st.session_state['selected_trade_idx'] is not None:
    regions = trades[st.session_state['selected_trade_idx']]['regions']

if regions:
    for idx, region in enumerate(regions):
        st.markdown(
            f"<tr>"
            f"<td>{idx+1}</td>"
            f"<td>{region['Category']}</td>"
            f"<td>{region['Feature 1']}</td>"
            f"<td>{region['Feature 2']}</td>"
            f"<td>{region['Start Date']}</td>"
            f"<td>{region['Start Candle']}</td>"
            f"<td>{region['End Date']}</td>"
            f"<td>{region['End Candle']}</td>"
            f"<td>{region['Key Price']}</td>"
            f"<td>{region['Tags']}</td>"
            f"<td>{region['Notes']}</td>"
            f"<td class='plus-btn'></td></tr>",
            unsafe_allow_html=True
        )
# Always an empty row with "+" at right for adding
st.markdown(
    "<tr><td colspan='11'></td><td class='plus-btn'>+</td></tr></table></div>", unsafe_allow_html=True)

# --- Main Chart ---
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    hovertext=[
        f"Idx:{i} {row['time']}<br>Open:{row['open']}<br>Close:{row['close']}" for i, row in df.iterrows()
    ],
    name="Candles"
)])
# Plot regions for current trade
if regions:
    for region in regions:
        color = {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(region["Category"], "grey")
        fig.add_vrect(
            x0=df.loc[region["Start Candle"], 'time'],
            x1=df.loc[region["End Candle"], 'time'],
            fillcolor=color, opacity=0.3, layer="below", line_width=0,
            annotation_text=region["Category"], annotation_position="top left"
        )
        fig.add_vline(x=df.loc[region["Start Candle"], 'time'], line_width=2, line_color=color)
        fig.add_vline(x=df.loc[region["End Candle"], 'time'], line_width=2, line_color=color)
fig.update_layout(
    xaxis_rangeslider_visible=False,
    dragmode="zoom",
    margin=dict(l=0, r=0, t=0, b=0),
    height=600,
    showlegend=False,
    plot_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    paper_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    font_color="#f5f5f5" if st.session_state['theme'] == "dark" else "#202020"
)
st.plotly_chart(fig, use_container_width=True)
