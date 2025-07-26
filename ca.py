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

# ========== SESSION STATE ==========
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}
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
if 'show_add_trade' not in st.session_state:
    st.session_state['show_add_trade'] = False
if 'show_add_region' not in st.session_state:
    st.session_state['show_add_region'] = False

# ========== HELPERS ==========
def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')

def get_eye(show):
    return "👁️" if show else "👁️‍🗨️"

# ========== LEFT SIDEBAR (TOOLS) ==========
if st.session_state['show_left_sidebar']:
    with st.sidebar:
        st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;">'
                    '<span style="font-size:20px;font-weight:600;">Tools</span>'
                    '<span style="cursor:pointer;font-size:22px;color:#999;" '
                    'onclick="window.parent.postMessage({streamlitCloseSidebar: \'left\'}, \'*\')">×</span>'
                    '</div>', unsafe_allow_html=True)
        st.write('<script>'
                 'window.addEventListener("message",e=>{if(e.data.streamlitCloseSidebar==="left"){window.parent.document.querySelector("aside[data-testid=\'stSidebar\']").style.display="none";fetch("/_stcore/closeleft");}});'
                 '</script>', unsafe_allow_html=True)

        # Region/trade annotation tools
        st.markdown("#### Region/Trade Annotation")
        region_type = st.selectbox("Region Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="tool_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="tool_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="tool_feature2")
        note = st.text_area("Notes/Observations", key="tool_notes")

        # Apply tools to current region in edit/create mode
        if st.session_state.get('edit_region_idx') is not None and st.session_state.get('selected_trade_id'):
            trade = st.session_state['trades'][st.session_state['selected_trade_id']]
            idx = st.session_state['edit_region_idx']
            if st.button("Apply Annotation", key="tool_apply"):
                region = trade["regions"][idx]
                region.update({
                    'category': region_type,
                    'feature1': feature1,
                    'feature2': feature2,
                    'notes': note
                })
                st.success("Region updated with new annotation!")
                st.experimental_rerun()

if not st.session_state['show_left_sidebar']:
    left_toggle_slot = st.empty()
    with left_toggle_slot:
        if st.button("≪", key="show_left_sidebar", help="Show Tools Sidebar"):
            st.session_state['show_left_sidebar'] = True
            st.experimental_rerun()

# ========== RIGHT SIDEBAR (DIRECTIONS) ==========
if st.session_state['show_right_sidebar']:
    st.markdown(
        '<div style="position:fixed;top:0;right:0;width:300px;height:100vh;'
        'background-color:#f8f9fa;z-index:1001;padding:24px 16px 16px 16px;border-left:1.5px solid #e5e5e5;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
        '<span style="font-size:20px;font-weight:600;">Directions</span>'
        '<span style="cursor:pointer;font-size:22px;color:#999;" id="close-right-sidebar">×</span>'
        '</div>'
        '<div style="font-size:15px;line-height:1.4;">'
        '<ul>'
        '<li>Click <b>+</b> to add a trade or region.</li>'
        '<li>Use <b>eye</b> icons to show/hide items on chart.</li>'
        '<li>Click any trade row to view/edit its regions below.</li>'
        '<li>Hover candlesticks for index/date.</li>'
        '<li>Annotation tools (left) update regions instantly.</li>'
        '<li>Click <b>✎</b> to edit, <b>×</b> to delete.</li>'
        '</ul>'
        '<br><i>Sidebars can be hidden or shown at any time.</i>'
        '</div></div>'
        '<script>document.getElementById("close-right-sidebar").onclick = () => {window.parent.postMessage({streamlitCloseSidebar:"right"}, "*");};</script>',
        unsafe_allow_html=True
    )
    st.write('<script>window.addEventListener("message",e=>{if(e.data.streamlitCloseSidebar==="right"){document.querySelectorAll("div[style*=position\\:fixed]").forEach(d=>d.style.display="none");fetch("/_stcore/closeright");}});</script>', unsafe_allow_html=True)

if not st.session_state['show_right_sidebar']:
    right_toggle_slot = st.empty()
    with right_toggle_slot:
        if st.button("≫", key="show_right_sidebar", help="Show Directions/Help Sidebar"):
            st.session_state['show_right_sidebar'] = True
            st.experimental_rerun()

# ========== MAIN CHART ==========
st.title("Stock Trade Region Annotator")
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

# ========== TRADES PANEL BELOW CHART ==========
st.markdown("### Trades")
if not st.session_state['trades']:
    trade_cols = st.columns([1, 4, 2, 1, 1])
    with trade_cols[0]: st.write("👁️")
    with trade_cols[1]: st.write("Trade # / Name")
    with trade_cols[2]: st.write("# Regions")
    with trade_cols[3]: st.write("➕")
    with trade_cols[4]: st.write("×")
    add_trade_col = st.columns([10, 1])
    with add_trade_col[1]:
        if st.button("➕", key="add_first_trade", help="Add Trade"):
            st.session_state['show_add_trade'] = True
else:
    for tid, trade in st.session_state['trades'].items():
        cols = st.columns([1, 4, 2, 1, 1])
        with cols[0]:
            newval = st.checkbox(get_eye(trade.get('show', False)), value=trade.get('show', False), key=f"show_trade_{tid}", label_visibility='collapsed')
            st.session_state['trades'][tid]['show'] = newval
        with cols[1]:
            button_label = f"**#{tid}: {trade['name']}**"
            if st.button(button_label, key=f"trade_button_{tid}"):
                st.session_state['selected_trade_id'] = tid
                st.session_state['edit_region_idx'] = None
                st.session_state['show_add_region'] = False
        with cols[2]:
            st.write(f"{len(trade['regions'])}")
        with cols[3]:
            if st.session_state.get('selected_trade_id') == tid:
                if st.button("➕", key=f"add_region_{tid}"):
                    st.session_state['show_add_region'] = True
                    st.session_state['edit_region_idx'] = None
        with cols[4]:
            if st.button("×", key=f"delete_trade_{tid}"):
                del st.session_state['trades'][tid]
                if st.session_state.get('selected_trade_id') == tid:
                    st.session_state['selected_trade_id'] = None
                st.experimental_rerun()
    add_row = st.columns([10, 1])
    with add_row[1]:
        if st.button("➕", key="add_new_trade", help="Add Trade"):
            st.session_state['show_add_trade'] = True

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
    if not trade['regions']:
        region_cols = st.columns([1, 3, 3, 2, 2, 2, 1, 1])
        with region_cols[0]: st.write("👁️")
        with region_cols[1]: st.write("Category")
        with region_cols[2]: st.write("Feature(s)")
        with region_cols[3]: st.write("Start")
        with region_cols[4]: st.write("End")
        with region_cols[5]: st.write("Key Price")
        with region_cols[6]: st.write("✎")
        with region_cols[7]:
            if st.button("➕", key="add_first_region"):
                st.session_state['show_add_region'] = True
    else:
        for i, region in enumerate(trade["regions"]):
            cols = st.columns([1, 3, 3, 2, 2, 2, 1, 1])
            with cols[0]:
                show = st.checkbox(get_eye(region.get('show', True)), value=region.get('show', True), key=f"show_region_{trade['name']}_{region['region_id']}", label_visibility='collapsed')
                trade["regions"][i]["show"] = show
            with cols[1]:
                st.write(region.get("category", ""))
            with cols[2]:
                feats = ", ".join([region.get("feature1", ""), region.get("feature2", "")])
                st.write(feats)
            with cols[3]:
                st.write(f"{region['start_idx']} ({region['start_time'][:10]})")
            with cols[4]:
                st.write(f"{region['end_idx']} ({region['end_time'][:10]})")
            with cols[5]:
                st.write(region["key_price"])
            with cols[6]:
                if st.button("✎", key=f"edit_region_{trade['name']}_{region['region_id']}"):
                    st.session_state['edit_region_idx'] = i
                    st.session_state['show_add_region'] = False
            with cols[7]:
                if st.button("×", key=f"delete_region_{trade['name']}_{region['region_id']}"):
                    trade["regions"].pop(i)
                    st.experimental_rerun()
            if st.session_state.get('edit_region_idx') == i:
                with st.expander(f"Edit Region {region['region_id']}", expanded=True):
                    start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=region["start_idx"], step=1, key=f"edit_region_start_idx_{i}")
                    end_idx = st.number_input("End Index", min_value=start_idx+1, max_value=max_idx, value=region["end_idx"], step=1, key=f"edit_region_end_idx_{i}")
                    category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"],
                                            index=["Bullish Run-Up", "Bearish Run-Down", "Entry Region"].index(region.get('category', 'Entry Region')),
                                            key=f"edit_region_category_{i}")
                    feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], index=0, key=f"edit_region_feature1_{i}")
                    feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], index=0, key=f"edit_region_feature2_{i}")
                    key_price = st.number_input("Key Price (Target/Stop/Entry)", value=float(region['key_price']), step=0.01, format="%.2f", key=f"edit_region_key_price_{i}")
                    notes = st.text_area("Notes", value=region.get("notes", ""), key=f"edit_region_notes_{i}")
                    if st.button("Update Region", key=f"btn_update_edit_region_{i}"):
                        trade["regions"][i] = {
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
                    if st.button("Cancel", key=f"btn_cancel_edit_region_{i}"):
                        st.session_state['edit_region_idx'] = None
                        st.experimental_rerun()
    if st.session_state.get('show_add_region', False):
        with st.expander("Add Region", expanded=True):
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
else:
    st.info("Select a trade above to view/add regions.")
