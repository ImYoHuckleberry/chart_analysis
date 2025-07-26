import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# --- Data Loading ---
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    df['candle_idx'] = df.index
    return df

df = load_data()
max_idx = len(df) - 1

st.set_page_config(layout="wide")

# --- Session State Initialization ---
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}  # {trade_id: {'name': str, 'regions': [region_dict, ...], 'show': bool}}
if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1
if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None
if 'show_add_trade' not in st.session_state:
    st.session_state['show_add_trade'] = False
if 'show_add_region' not in st.session_state:
    st.session_state['show_add_region'] = False
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None

def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')

# --- SIDEBAR TOOLBOX ---
st.sidebar.title("Feature ID Toolbox")
st.sidebar.markdown("""
**Legend:**
- <span style='color:green'>Green</span>: Bullish Run-Up / Price Target
- <span style='color:red'>Red</span>: Bearish Run-Down / Stop Loss
- <span style='color:blue'>Blue</span>: Entry Region
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Workflow:**")
st.sidebar.markdown("""
1. Add trades and regions using the buttons below the chart.
2. Use [Show/Hide] to control visibility.
3. Click [Select] to work with regions in a trade.
4. Hover candles for **Index** (for region input).
""")
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Tips:**  
- Use index for region boundaries (see chart tooltip).
- Use “Edit” to update or correct a region.
- All controls are below the chart.
""")

# --- CHART: Only show regions/trades toggled to show ---
st.title("Stock Trade Region Annotator (Table-driven UI)")

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
        annotation_text=region['category'], annotation_position="top left"
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

# --- TRADES TABLE AND BUTTONS ---
st.markdown("### Trades")

trade_cols_header = st.columns([1,1,1,5,2,2])
trade_cols_header[0].write("Show")
trade_cols_header[1].write("Select")
trade_cols_header[2].write("Delete")
trade_cols_header[3].write("Name")
trade_cols_header[4].write("Regions")
trade_cols_header[5].write("Add")

trade_ids = sorted(st.session_state['trades'].keys())
for tid in trade_ids:
    trade = st.session_state['trades'][tid]
    cols = st.columns([1,1,1,5,2,2])
    # Show/Hide checkbox
    with cols[0]:
        show = st.checkbox("", key=f"show_trade_{tid}", value=trade.get("show", False))
        st.session_state['trades'][tid]["show"] = show
    # Select button
    with cols[1]:
        if st.button("Select", key=f"select_trade_{tid}"):
            st.session_state['selected_trade_id'] = tid
            st.session_state['show_add_region'] = False
            st.session_state['edit_region_idx'] = None
    # Delete button
    with cols[2]:
        if st.button("❌", key=f"del_trade_{tid}"):
            del st.session_state['trades'][tid]
            if st.session_state.get('selected_trade_id') == tid:
                st.session_state['selected_trade_id'] = None
            st.experimental_rerun()
    # Trade Name
    with cols[3]:
        st.write(trade["name"])
    # Region count
    with cols[4]:
        st.write(len(trade["regions"]))
    # Add Region button (appears for selected trade only)
    with cols[5]:
        if st.session_state.get('selected_trade_id') == tid:
            if st.button("Add Region", key=f"add_region_{tid}"):
                st.session_state['show_add_region'] = True
                st.session_state['edit_region_idx'] = None

# Add Trade button
if st.button("Add Trade"):
    st.session_state['show_add_trade'] = True
    st.session_state['selected_trade_id'] = None
    st.session_state['show_add_region'] = False
    st.session_state['edit_region_idx'] = None

# --- ADD TRADE PANEL ---
if st.session_state.get('show_add_trade', False):
    with st.expander("Create New Trade", expanded=True):
        trade_name = st.text_input("Trade Name", key="new_trade_name")
        if st.button("Create Trade", key="btn_create_trade"):
            # Unique trade number enforcement
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

# --- REGIONS TABLE AND BUTTONS ---
if st.session_state.get('selected_trade_id') in st.session_state['trades']:
    trade = st.session_state['trades'][st.session_state['selected_trade_id']]
    st.markdown(f"### Regions for Trade: **{trade['name']}**")
    region_cols_header = st.columns([1,1,1,3,2,2,2,2])
    region_cols_header[0].write("Show")
    region_cols_header[1].write("Edit")
    region_cols_header[2].write("Delete")
    region_cols_header[3].write("Category")
    region_cols_header[4].write("Start (Idx)")
    region_cols_header[5].write("End (Idx)")
    region_cols_header[6].write("Key Price")
    region_cols_header[7].write("Notes")

    for i, region in enumerate(trade["regions"]):
        cols = st.columns([1,1,1,3,2,2,2,2])
        # Show/Hide checkbox
        with cols[0]:
            show = st.checkbox("", key=f"show_region_{trade['name']}_{region['region_id']}", value=region.get("show", True))
            trade["regions"][i]["show"] = show
        # Edit button
        with cols[1]:
            if st.button("Edit", key=f"edit_region_{trade['name']}_{region['region_id']}"):
                st.session_state['edit_region_idx'] = i
                st.session_state['show_add_region'] = False
        # Delete button
        with cols[2]:
            if st.button("❌", key=f"del_region_{trade['name']}_{region['region_id']}"):
                trade["regions"].pop(i)
                st.experimental_rerun()
        # Category, Start, End, Price, Notes
        with cols[3]:
            st.write(region["category"])
        with cols[4]:
            st.write(f"{region['start_idx']} ({region['start_time'][:10]})")
        with cols[5]:
            st.write(f"{region['end_idx']} ({region['end_time'][:10]})")
        with cols[6]:
            st.write(region["key_price"])
        with cols[7]:
            st.write(region["notes"])

    # --- ADD REGION PANEL ---
    if st.session_state.get('show_add_region', False):
        with st.expander("Add Region", expanded=True):
            # Indexes
            start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=10, step=1, key="add_region_start_idx")
            end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=start_idx+5, step=1, key="add_region_end_idx")
            # Category
            category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="add_region_category")
            key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(df.loc[end_idx, 'close']), step=0.01, format="%.2f", key="add_region_key_price")
            tags = st.text_input("Tags", key="add_region_tags")
            notes = st.text_area("Notes", key="add_region_notes")
            if st.button("Save Region", key="btn_save_add_region"):
                region = {
                    'region_id': len(trade["regions"]) + 1,
                    'category': category,
                    'key_price': key_price,
                    'tags': tags,
                    'notes': notes,
                    'symbol': "AMD",
                    'interval': "1D",
                    'start_idx': int(start_idx),
                    'end_idx': int(end_idx),
                    'start_time': df.loc[int(start_idx), 'time'],
                    'end_time': df.loc[int(end_idx), 'time'],
                    'color': region_color(category),
                    'show': True
                }
                trade['regions'].append(region)
                st.session_state['show_add_region'] = False
                st.success("Region added.")
                st.experimental_rerun()
            if st.button("Cancel", key="btn_cancel_add_region"):
                st.session_state['show_add_region'] = False
                st.experimental_rerun()

    # --- EDIT REGION PANEL ---
    if st.session_state.get('edit_region_idx') is not None and 0 <= st.session_state['edit_region_idx'] < len(trade["regions"]):
        edit_idx = st.session_state['edit_region_idx']
        region = trade["regions"][edit_idx]
        with st.expander(f"Edit Region {region['region_id']}", expanded=True):
            start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=region["start_idx"], step=1, key="edit_region_start_idx")
            end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=region["end_idx"], step=1, key="edit_region_end_idx")
            category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"],
                                    index=["Bullish Run-Up", "Bearish Run-Down", "Entry Region"].index(region['category']), key="edit_region_category")
            key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(region['key_price']), step=0.01, format="%.2f", key="edit_region_key_price")
            tags = st.text_input("Tags", value=region["tags"], key="edit_region_tags")
            notes = st.text_area("Notes", value=region["notes"], key="edit_region_notes")
            if st.button("Update Region", key="btn_update_edit_region"):
                trade["regions"][edit_idx] = {
                    **region,
                    'category': category,
                    'key_price': key_price,
                    'tags': tags,
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
            if st.button("Cancel", key="btn_cancel_edit_region"):
                st.session_state['edit_region_idx'] = None
                st.experimental_rerun()
