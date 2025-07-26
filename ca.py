import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# ========== DATA LOADING ==========
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    df['candle_idx'] = df.index
    return df

df = load_data()
max_idx = len(df) - 1

# ========== SESSION STATE INIT ==========
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}  # {trade_id: {name, regions, show}}
if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1
if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None
if 'show_left_sidebar' not in st.session_state:
    st.session_state['show_left_sidebar'] = True
if 'show_right_sidebar' not in st.session_state:
    st.session_state['show_right_sidebar'] = True
if 'show_bottom_panel' not in st.session_state:
    st.session_state['show_bottom_panel'] = True
if 'show_add_trade' not in st.session_state:
    st.session_state['show_add_trade'] = False
if 'show_add_region' not in st.session_state:
    st.session_state['show_add_region'] = False

# Helper for color
def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')

# ========== SIDEBAR CONTROLS ==========
if st.session_state['show_left_sidebar']:
    with st.sidebar:
        st.markdown("### Tools: Region/Trade Labeling")
        # Feature category and annotation tools
        region_type = st.selectbox("Region Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="tool_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="tool_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="tool_feature2")
        confidence = st.slider("Confidence in Label", 1, 10, 7, key="tool_confidence")
        note = st.text_area("Notes for Region", key="tool_notes")
        # Button to apply tools to currently selected region (in edit mode)
        if st.session_state.get('edit_region_idx') is not None and st.session_state.get('selected_trade_id'):
            trade = st.session_state['trades'][st.session_state['selected_trade_id']]
            if st.button("Apply Tools to Region", key="tool_apply"):
                idx = st.session_state['edit_region_idx']
                region = trade["regions"][idx]
                # update all feature info
                region.update({
                    'category': region_type,
                    'feature1': feature1,
                    'feature2': feature2,
                    'confidence': confidence,
                    'notes': note
                })
                st.success("Region updated with new feature/categorization!")
                st.experimental_rerun()
        st.markdown("---")
        # Hide sidebar
        if st.button("Hide Tools Sidebar", key="hide_left_sidebar"):
            st.session_state['show_left_sidebar'] = False

# Show/hide right sidebar (for instructions)
right_sidebar_slot = st.empty()
if st.session_state['show_right_sidebar']:
    with right_sidebar_slot.container():
        st.markdown("### Directions / Workflow (Click to Hide)", unsafe_allow_html=True)
        st.info("""
**Directions:**  
- Add trades below the chart using "Add Trade."
- Toggle 👁️ to show/hide trades and regions.
- Click a trade row (number or name) to select and view regions.
- All region labeling and feature tagging tools are at the left.
- Hover a candle for its index/date.
- Use the ✎ to edit regions (with left sidebar tools for labeling).
- Hide/show any sidebar or bottom panel as desired.

**Keyboard Shortcuts:** (when supported by browser)
- [ ] for rapid navigation coming soon
""")
        if st.button("Hide Directions Sidebar", key="hide_right_sidebar"):
            st.session_state['show_right_sidebar'] = False

# Unhide controls
unhide_cols = st.columns([1,6,1])
with unhide_cols[0]:
    if not st.session_state['show_left_sidebar']:
        if st.button("Show Tools Sidebar", key="show_left_sidebar"):
            st.session_state['show_left_sidebar'] = True
with unhide_cols[2]:
    if not st.session_state['show_right_sidebar']:
        if st.button("Show Directions Sidebar", key="show_right_sidebar"):
            st.session_state['show_right_sidebar'] = True

# ========== MAIN CHART ==========
st.title("Stock Trade Region Annotator")

# Only show regions/trades toggled to show
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
    margin=dict(l=20, r=20, t=20, b=20),
    height=600,
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# ========== SHOW/HIDE BOTTOM PANEL ==========
hide_panel_btn_col = st.columns([9,1])
if hide_panel_btn_col[1].button("Hide Bottom Panel" if st.session_state['show_bottom_panel'] else "Show Bottom Panel", key="toggle_bottom_panel"):
    st.session_state['show_bottom_panel'] = not st.session_state['show_bottom_panel']
if not st.session_state['show_bottom_panel']:
    st.stop()

# ========== TRADES TABLE (BELOW CHART) ==========
st.markdown("### Trades")

def get_eye(show):
    return "👁️" if show else "👁️‍🗨️"

def get_trash(disabled=False):
    return f"<span style='color:gray; opacity:{'0.3' if disabled else '0.9'};'>🗑️</span>"

def trade_row_style(selected=False):
    return "background-color: #e6f4ff;" if selected else ""

for tid, trade in st.session_state['trades'].items():
    # Table row
    cols = st.columns([1,4,2,2,1,1])
    # Eye toggle
    with cols[0]:
        newval = st.checkbox(get_eye(trade.get('show', False)), value=trade.get('show', False), key=f"show_trade_{tid}", label_visibility='collapsed')
        st.session_state['trades'][tid]['show'] = newval
    # Trade number and name (clickable)
    with cols[1]:
        button_label = f"**#{tid}: {trade['name']}**"
        if st.button(button_label, key=f"trade_button_{tid}"):
            st.session_state['selected_trade_id'] = tid
            st.session_state['edit_region_idx'] = None
            st.session_state['show_add_region'] = False
    # Region count
    with cols[2]:
        st.write(f"{len(trade['regions'])}")
    # Add region button
    with cols[3]:
        if st.session_state.get('selected_trade_id') == tid:
            if st.button("➕", key=f"add_region_{tid}"):
                st.session_state['show_add_region'] = True
                st.session_state['edit_region_idx'] = None
    # Trash (delete) icon
    with cols[4]:
        if st.button("×", key=f"delete_trade_{tid}"):
            del st.session_state['trades'][tid]
            if st.session_state.get('selected_trade_id') == tid:
                st.session_state['selected_trade_id'] = None
            st.experimental_rerun()
    # Highlight selected trade
    with cols[5]:
        if st.session_state.get('selected_trade_id') == tid:
            st.markdown("<span style='color:#1995ff; font-weight:bold;'>&#10003;</span>", unsafe_allow_html=True)

# Add Trade button
if st.button("Add Trade"):
    st.session_state['show_add_trade'] = True
    st.session_state['show_add_region'] = False
    st.session_state['edit_region_idx'] = None

# ========== ADD TRADE PANEL ==========
if st.session_state.get('show_add_trade', False):
    with st.expander("Create New Trade", expanded=True):
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

# ========== REGIONS TABLE FOR SELECTED TRADE ==========
if st.session_state.get('selected_trade_id') in st.session_state['trades']:
    trade = st.session_state['trades'][st.session_state['selected_trade_id']]
    st.markdown(f"### Regions for Trade: **{trade['name']}**")
    for i, region in enumerate(trade["regions"]):
        cols = st.columns([1,3,3,2,2,2,1,1])
        # Eye toggle
        with cols[0]:
            show = st.checkbox(get_eye(region.get('show', True)), value=region.get('show', True), key=f"show_region_{trade['name']}_{region['region_id']}", label_visibility='collapsed')
            trade["regions"][i]["show"] = show
        # Category
        with cols[1]:
            st.write(region.get("category", ""))
        # Feature(s)
        with cols[2]:
            st.write(region.get("feature1", ""))
        # Start
        with cols[3]:
            st.write(f"{region['start_idx']} ({region['start_time'][:10]})")
        # End
        with cols[4]:
            st.write(f"{region['end_idx']} ({region['end_time'][:10]})")
        # Key price
        with cols[5]:
            st.write(region["key_price"])
        # Edit
        with cols[6]:
            if st.button("✎", key=f"edit_region_{trade['name']}_{region['region_id']}"):
                st.session_state['edit_region_idx'] = i
                st.session_state['show_add_region'] = False
        # Trash
        with cols[7]:
            if st.button("×", key=f"delete_region_{trade['name']}_{region['region_id']}"):
                trade["regions"].pop(i)
                st.experimental_rerun()
        # --- Edit panel below the row ---
        if st.session_state.get('edit_region_idx') == i:
            with st.expander(f"Edit Region {region['region_id']}", expanded=True):
                start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=region["start_idx"], step=1, key=f"edit_region_start_idx_{i}")
                end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=region["end_idx"], step=1, key=f"edit_region_end_idx_{i}")
                category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"],
                                        index=["Bullish Run-Up", "Bearish Run-Down", "Entry Region"].index(region.get('category', 'Entry Region')),
                                        key=f"edit_region_category_{i}")
                feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], index=0, key=f"edit_region_feature1_{i}")
                feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], index=0, key=f"edit_region_feature2_{i}")
                confidence = st.slider("Confidence in Label", 1, 10, int(region.get('confidence', 7)), key=f"edit_region_confidence_{i}")
                key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(region['key_price']), step=0.01, format="%.2f", key=f"edit_region_key_price_{i}")
                notes = st.text_area("Notes", value=region.get("notes", ""), key=f"edit_region_notes_{i}")
                if st.button("Update Region", key=f"btn_update_edit_region_{i}"):
                    trade["regions"][i] = {
                        **region,
                        'category': category,
                        'feature1': feature1,
                        'feature2': feature2,
                        'confidence': confidence,
                        'notes': notes,
                        'start_idx': int(start_idx),
                        'end_idx': int(end_idx),
                        'start_time': df.loc[int(start_idx), 'time'],
                        'end_time': df.loc[int(end_idx), 'time'],
                        'color': region_color(category)
                    }
                    st.session_state['edit_region_idx'] = None
                    st.success("Region updated.")
                    st.experimental_rerun()
                if st.button("Cancel", key=f"btn_cancel_edit_region_{i}"):
                    st.session_state['edit_region_idx'] = None
                    st.experimental_rerun()

    # ========== ADD REGION PANEL ==========
    if st.session_state.get('show_add_region', False):
        with st.expander("Add Region", expanded=True):
            start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=10, step=1, key="add_region_start_idx")
            end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=start_idx+5, step=1, key="add_region_end_idx")
            category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="add_region_category")
            feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="add_region_feature1")
            feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="add_region_feature2")
            confidence = st.slider("Confidence in Label", 1, 10, 7, key="add_region_confidence")
            key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(df.loc[end_idx, 'close']), step=0.01, format="%.2f", key="add_region_key_price")
            notes = st.text_area("Notes", key="add_region_notes")
            if st.button("Save Region", key="btn_save_add_region"):
                region = {
                    'region_id': len(trade["regions"]) + 1,
                    'category': category,
                    'feature1': feature1,
                    'feature2': feature2,
                    'confidence': confidence,
                    'notes': notes,
                    'symbol': "AMD",
                    'interval': "1D",
                    'start_idx': int(start_idx),
                    'end_idx': int(end_idx),
                    'start_time': df.loc[int(start_idx), 'time'],
                    'end_time': df.loc[int(end_idx), 'time'],
                    'color': region_color(category),
                    'show': True,
                    'key_price': key_price
                }
                trade['regions'].append(region)
                st.session_state['show_add_region'] = False
                st.success("Region added.")
                st.experimental_rerun()
            if st.button("Cancel", key="btn_cancel_add_region"):
                st.session_state['show_add_region'] = False
                st.experimental_rerun()
