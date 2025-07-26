import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# ==== DATA LOADING ====
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    df['candle_idx'] = df.index
    return df

df = load_data()
max_idx = len(df) - 1

# ==== THEME (LIGHT / DARK) ====
if 'theme' not in st.session_state:
    st.session_state['theme'] = "dark"
if 'show_left_sidebar' not in st.session_state:
    st.session_state['show_left_sidebar'] = True
if 'show_right_sidebar' not in st.session_state:
    st.session_state['show_right_sidebar'] = True

# Apply light/dark theme
if st.session_state['theme'] == "dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #171717; color: #f5f5f5; }
        .stDataFrame, .css-1v0mbdj, .stTable, .stMarkdown { background: #232323; color: #f5f5f5; }
        th { background: #232323 !important; color: #f5f5f5 !important; }
        td { background: #232323 !important; color: #f5f5f5 !important; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #fafafa; color: #202020; }
        .stDataFrame, .css-1v0mbdj, .stTable, .stMarkdown { background: #fff; color: #202020; }
        th { background: #f4f4f4 !important; color: #202020 !important; }
        td { background: #fff !important; color: #202020 !important; }
        </style>
        """, unsafe_allow_html=True)

# ==== SESSION STATE ====
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}
if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1
if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None
if 'show_add_trade' not in st.session_state:
    st.session_state['show_add_trade'] = False
if 'show_add_region' not in st.session_state:
    st.session_state['show_add_region'] = False
if 'last_selected_region' not in st.session_state:
    st.session_state['last_selected_region'] = None

def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')

def get_eye(show):
    return "👁️" if show else "👁️‍🗨️"

# ==== TOP BAR: THEME & SIDEBAR TOGGLES ====
top_cols = st.columns([2, 1, 1, 1])
with top_cols[0]:
    st.title("Stock Trade Region Annotator")
with top_cols[1]:
    theme_toggle = st.toggle("Night Mode", value=(st.session_state['theme'] == "dark"), key="theme_toggle")
    if theme_toggle and st.session_state['theme'] != "dark":
        st.session_state['theme'] = "dark"
        st.experimental_rerun()
    elif not theme_toggle and st.session_state['theme'] != "light":
        st.session_state['theme'] = "light"
        st.experimental_rerun()
with top_cols[2]:
    if st.session_state['show_left_sidebar']:
        if st.button("«", help="Hide Tools"):
            st.session_state['show_left_sidebar'] = False
            st.experimental_rerun()
    else:
        if st.button("»", help="Show Tools"):
            st.session_state['show_left_sidebar'] = True
            st.experimental_rerun()
with top_cols[3]:
    if st.session_state['show_right_sidebar']:
        if st.button("×", help="Hide Directions"):
            st.session_state['show_right_sidebar'] = False
            st.experimental_rerun()
    else:
        if st.button("?", help="Show Directions"):
            st.session_state['show_right_sidebar'] = True
            st.experimental_rerun()

# ==== LEFT SIDEBAR: TOOLS ====
if st.session_state['show_left_sidebar']:
    with st.sidebar:
        st.markdown("### Tools for Region Annotation")
        region_type = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="tool_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="tool_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="tool_feature2")
        note = st.text_area("Notes/Observations", key="tool_notes")
        st.markdown("---")
        st.caption("This panel is always visible for quick annotation when editing or creating a region.")

# ==== RIGHT SIDEBAR: DIRECTIONS ====
if st.session_state['show_right_sidebar']:
    st.markdown(
        """
        <div style='position:fixed;right:0;top:60px;width:270px;height:85vh;overflow:auto;
        background:#232323;padding:20px 10px 10px 20px;border-left:2px solid #444;z-index:9999;'>
        <div style='font-size:20px;font-weight:bold;margin-bottom:7px;'>Directions</div>
        <ul style='font-size:15px;'>
        <li>Use <b>+</b> in tables to add a trade or region.</li>
        <li>Use <b>Edit</b> to modify, <b>×</b> to delete.</li>
        <li>Click a trade row to select and show its regions.</li>
        <li>Regions: Bullish Run-Up, Bearish Run-Down, Entry Region (one or all per trade).</li>
        <li>Left sidebar = tools for quick feature/annotation selection.</li>
        <li>Chart is fully interactive, hover for index/date info.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==== RESPONSIVE MAIN CHART ====
regions_to_plot = []
for tid, trade in st.session_state['trades'].items():
    if trade.get('show', False):
        for region in trade['regions']:
            if region.get('show', True):
                regions_to_plot.append(region)

hovertexts = [
    f"Index: {idx}<br>Date: {row['time']}<br>Open: {row['open']}<br>High: {row['high']}<br>Low: {row['low']}<br>Close: {row['close']}"
    for idx, row in df.iterrows()
]
fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    hovertext=hovertexts,
    name="Candles"
)])
for region in regions_to_plot:
    fig.add_vrect(
        x0=df.loc[region['start_idx'], 'time'],
        x1=df.loc[region['end_idx'], 'time'],
        fillcolor=region['color'], opacity=0.3,
        layer="below", line_width=0,
        annotation_text=region.get('category', ''), annotation_position="top left"
    )
    fig.add_vline(x=df.loc[region['start_idx'], 'time'], line_width=2, line_color=region['color'])
    fig.add_vline(x=df.loc[region['end_idx'], 'time'], line_width=2, line_color=region['color'])
fig.update_layout(
    xaxis_rangeslider_visible=False,
    dragmode="zoom",
    margin=dict(l=0, r=0, t=10, b=10),
    height=500,
    width=None,  # Let Streamlit auto-scale
    showlegend=False,
    plot_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    paper_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    font_color="#f5f5f5" if st.session_state['theme'] == "dark" else "#202020"
)
st.plotly_chart(fig, use_container_width=True)

# ==== TRADES TABLE (BELOW CHART) ====
st.markdown("#### Trades")
trade_headers = ["Trade #", "Trade Name", "Entry Date", "Exit Date", "Edit", "Delete"]
trade_data = []
for tid, trade in st.session_state['trades'].items():
    entry, exit = "", ""
    if trade['regions']:
        entry = trade['regions'][0]['start_time'][:10]
        exit = trade['regions'][-1]['end_time'][:10]
    trade_data.append([tid, trade['name'], entry, exit, "Edit", "Delete"])
trade_df = pd.DataFrame(trade_data, columns=trade_headers) if trade_data else pd.DataFrame(columns=trade_headers)
st.dataframe(trade_df, use_container_width=True, hide_index=True)

# Row action buttons
for idx, (tid, trade) in enumerate(st.session_state['trades'].items()):
    cols = st.columns([2, 6, 3, 3, 1, 1])
    with cols[0]: st.write(tid)
    with cols[1]: st.write(trade['name'])
    with cols[2]: st.write(trade_df.loc[idx, "Entry Date"])
    with cols[3]: st.write(trade_df.loc[idx, "Exit Date"])
    with cols[4]:
        if st.button("✎", key=f"edit_trade_{tid}"):
            st.session_state['selected_trade_id'] = tid
            st.session_state['edit_region_idx'] = None
    with cols[5]:
        if st.button("×", key=f"delete_trade_{tid}"):
            del st.session_state['trades'][tid]
            if st.session_state.get('selected_trade_id') == tid:
                st.session_state['selected_trade_id'] = None
            st.experimental_rerun()
# Plus button to add trade (empty row at bottom)
cols = st.columns([2, 6, 3, 3, 1, 1])
with cols[0]:
    if st.button("+", key="add_trade"):
        st.session_state['show_add_trade'] = True
        st.experimental_rerun()
with cols[1]: st.write("Add New Trade")
with cols[2]: st.write("")
with cols[3]: st.write("")
with cols[4]: st.write("")
with cols[5]: st.write("")

# ==== ADD TRADE PANEL ====
if st.session_state.get('show_add_trade', False):
    st.markdown("##### Add New Trade")
    trade_name = st.text_input("Trade Name", key="new_trade_name")
    if st.button("Create Trade", key="btn_create_trade"):
        while st.session_state['trade_id_counter'] in st.session_state['trades']:
            st.session_state['trade_id_counter'] += 1
        new_trade_id = st.session_state['trade_id_counter']
        st.session_state['trades'][new_trade_id] = {'name': trade_name, 'regions': [], 'show': True}
        st.session_state['selected_trade_id'] = new_trade_id
        st.session_state['trade_id_counter'] += 1
        st.session_state['show_add_trade'] = False
        st.success(f"Trade #{new_trade_id} '{trade_name}' created.")
        st.experimental_rerun()
    if st.button("Cancel", key="btn_cancel_create_trade"):
        st.session_state['show_add_trade'] = False
        st.experimental_rerun()

# ==== REGIONS TABLE (FOR SELECTED TRADE) ====
st.markdown("#### Regions (Selected Trade)")
if st.session_state.get('selected_trade_id') in st.session_state['trades']:
    trade = st.session_state['trades'][st.session_state['selected_trade_id']]
    region_headers = ["Region #", "Category", "Start Date", "End Date", "Feature 1", "Feature 2", "Edit", "Delete"]
    region_data = []
    for idx, region in enumerate(trade["regions"]):
        region_data.append([
            idx + 1,
            region["category"],
            region["start_time"][:10],
            region["end_time"][:10],
            region.get("feature1", ""),
            region.get("feature2", ""),
            "Edit", "Delete"
        ])
    region_df = pd.DataFrame(region_data, columns=region_headers) if region_data else pd.DataFrame(columns=region_headers)
    st.dataframe(region_df, use_container_width=True, hide_index=True)
    for idx, region in enumerate(trade["regions"]):
        cols = st.columns([2, 4, 4, 4, 4, 4, 1, 1])
        with cols[0]: st.write(idx + 1)
        with cols[1]: st.write(region["category"])
        with cols[2]: st.write(region["start_time"][:10])
        with cols[3]: st.write(region["end_time"][:10])
        with cols[4]: st.write(region.get("feature1", ""))
        with cols[5]: st.write(region.get("feature2", ""))
        with cols[6]:
            if st.button("✎", key=f"edit_region_{st.session_state['selected_trade_id']}_{idx}"):
                st.session_state['edit_region_idx'] = idx
        with cols[7]:
            if st.button("×", key=f"delete_region_{st.session_state['selected_trade_id']}_{idx}"):
                trade["regions"].pop(idx)
                st.experimental_rerun()
    # Plus button for region
    cols = st.columns([2, 4, 4, 4, 4, 4, 1, 1])
    with cols[0]:
        if st.button("+", key="add_region"):
            st.session_state['show_add_region'] = True
            st.experimental_rerun()
    with cols[1]: st.write("Add New Region")
    with cols[2]: st.write("")
    with cols[3]: st.write("")
    with cols[4]: st.write("")
    with cols[5]: st.write("")
    with cols[6]: st.write("")
    with cols[7]: st.write("")

    # Edit or Add panel
    if st.session_state.get('show_add_region', False):
        st.markdown("##### Add Region")
        start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=10, step=1, key="add_region_start_idx")
        end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=start_idx+5, step=1, key="add_region_end_idx")
        category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="add_region_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="add_region_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="add_region_feature2")
        key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(df.loc[int(end_idx), 'close']), step=0.01, format="%.2f", key="add_region_key_price")
        notes = st.text_area("Notes", key="add_region_notes")
        if st.button("Save Region", key="btn_add_region"):
            region = {
                'region_id': len(trade["regions"]) + 1,
                'category': category,
                'feature1': feature1,
                'feature2': feature2,
                'notes': notes,
                'start_idx': int(start_idx),
                'end_idx': int(end_idx),
                'start_time': df.loc[int(start_idx), 'time'],
                'end_time': df.loc[int(end_idx), 'time'],
                'color': region_color(category),
                'show': True,
                'key_price': key_price
            }
            trade["regions"].append(region)
            st.session_state['show_add_region'] = False
            st.success("Region added.")
            st.experimental_rerun()
        if st.button("Cancel", key="btn_cancel_add_region"):
            st.session_state['show_add_region'] = False
            st.experimental_rerun()
    if st.session_state.get('edit_region_idx') is not None:
        idx = st.session_state['edit_region_idx']
        region = trade["regions"][idx]
        st.markdown(f"##### Edit Region #{idx + 1}")
        start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=region["start_idx"], step=1, key="edit_region_start_idx")
        end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=region["end_idx"], step=1, key="edit_region_end_idx")
        category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], index=["Bullish Run-Up", "Bearish Run-Down", "Entry Region"].index(region.get('category', 'Entry Region')), key="edit_region_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="edit_region_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="edit_region_feature2")
        key_price = st.number_input("Key Price (Target/Stop/Entry)", value=region["key_price"], step=0.01, format="%.2f", key="edit_region_key_price")
        notes = st.text_area("Notes", value=region.get('notes', ""), key="edit_region_notes")
        if st.button("Update Region", key="btn_update_region"):
            trade["regions"][idx] = {
                **region,
                'category': category,
                'feature1': feature1,
                'feature2': feature2,
                'notes': notes,
                'start_idx': int(start_idx),
                'end_idx': int(end_idx),
                'start_time': df.loc[int(start_idx), 'time'],
                'end_time': df.loc[int(end_idx), 'time'],
                'color': region_color(category),
                'show': True,
                'key_price': key_price
            }
            st.session_state['edit_region_idx'] = None
            st.success("Region updated.")
            st.experimental_rerun()
        if st.button("Cancel", key="btn_cancel_edit_region"):
            st.session_state['edit_region_idx'] = None
            st.experimental_rerun()
else:
    st.info("Select a trade above to view/add regions.")

