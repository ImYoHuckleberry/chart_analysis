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

# --- Session State ---
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}
if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1
if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None
if 'edit_trade_idx' not in st.session_state:
    st.session_state['edit_trade_idx'] = None
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None
if 'show_left_sidebar' not in st.session_state:
    st.session_state['show_left_sidebar'] = True
if 'show_right_sidebar' not in st.session_state:
    st.session_state['show_right_sidebar'] = True
if 'theme' not in st.session_state:
    st.session_state['theme'] = "dark"
if 'chart_height_sel' not in st.session_state:
    st.session_state['chart_height_sel'] = "Medium (600px)"

def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')
def get_eye(show):
    return "👁️" if show else "👁️‍🗨️"

# --- Theme: Style Inject ---
if st.session_state['theme'] == "dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #171717 !important; color: #f5f5f5 !important; }
        th { background: #232323 !important; color: #fafafa !important; font-size:15px; font-weight:bold; border-bottom:1px solid #444;}
        td { background: #232323 !important; color: #d3d3d3 !important; font-size:13px; font-weight:normal;}
        .sidebar-title { font-weight:bold; font-size:19px;}
        .sidebar-chevron { position:absolute;left:4px;top:2px;font-size:22px; }
        .minimal-table td, .minimal-table th { text-align: center; padding: 6px 6px; border-bottom:1px solid #333;}
        .minimal-table tr:last-child td { border-bottom:0;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #fafafa !important; color: #202020 !important; }
        th { background: #f4f4f4 !important; color: #222 !important; font-size:15px; font-weight:bold; border-bottom:1px solid #ddd;}
        td { background: #fff !important; color: #3a3a3a !important; font-size:13px; font-weight:normal;}
        .sidebar-title { font-weight:bold; font-size:19px;}
        .sidebar-chevron { position:absolute;left:4px;top:2px;font-size:22px; }
        .minimal-table td, .minimal-table th { text-align: center; padding: 6px 6px; border-bottom:1px solid #eee;}
        .minimal-table tr:last-child td { border-bottom:0;}
        </style>
        """, unsafe_allow_html=True)

# --- SIDEBAR: Left (Tools) ---
if st.session_state['show_left_sidebar']:
    with st.sidebar:
        left_chevron = st.button("«", help="Hide Tools", key="hide_tools_chevron")
        if left_chevron:
            st.session_state['show_left_sidebar'] = False
            st.experimental_rerun()
        st.markdown("<span class='sidebar-title'>Tools</span>", unsafe_allow_html=True)
        st.session_state['chart_height_sel'] = st.selectbox("Chart Height", ["Small (400px)", "Medium (600px)", "Large (900px)", "Full Window"], index=["Small (400px)", "Medium (600px)", "Large (900px)", "Full Window"].index(st.session_state['chart_height_sel']), key="chart_height_selbox")
        # Theme toggle
        theme_toggle = st.toggle("Night Mode", value=(st.session_state['theme'] == "dark"), key="theme_toggle")
        if theme_toggle and st.session_state['theme'] != "dark":
            st.session_state['theme'] = "dark"
            st.experimental_rerun()
        elif not theme_toggle and st.session_state['theme'] != "light":
            st.session_state['theme'] = "light"
            st.experimental_rerun()
        st.divider()
        st.markdown("#### Annotation Tools")
        tool_category = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="tool_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="tool_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="tool_feature2")
        note = st.text_area("Notes/Observations", key="tool_notes")
else:
    left_edge = st.button("»", help="Show Tools", key="show_tools_chevron")
    if left_edge:
        st.session_state['show_left_sidebar'] = True
        st.experimental_rerun()

# --- SIDEBAR: Right (Directions/Help) ---
if st.session_state['show_right_sidebar']:
    with st.container():
        right_chevron = st.button("»", help="Hide Directions", key="hide_dir_chevron")
        if right_chevron:
            st.session_state['show_right_sidebar'] = False
            st.experimental_rerun()
        st.markdown("<span class='sidebar-title'>Directions</span>", unsafe_allow_html=True)
        st.markdown(
            """
            - **Click "+"** to add new record in tables below chart.
            - **Use "✏️" to edit, "👁️" to toggle visibility, "−" to delete.**
            - **Click a trade row** to select and show regions.
            - **All region/trade editing via table icons.**
            """
        )
else:
    right_edge = st.button("«", help="Show Directions", key="show_dir_chevron", disabled=False)
    if right_edge:
        st.session_state['show_right_sidebar'] = True
        st.experimental_rerun()

# --- CHART HEIGHT SELECTION ---
chart_height_map = {
    "Small (400px)": 400,
    "Medium (600px)": 600,
    "Large (900px)": 900,
    "Full Window": 850,
}
chart_height = chart_height_map.get(st.session_state['chart_height_sel'], 600)

# --- MAIN CHART AREA ---
with st.container():
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)  # small top margin
    hovertexts = [
        f"Index: {idx}<br>Date: {row['time']}<br>Open: {row['open']}<br>High: {row['high']}<br>Low: {row['low']}<br>Close: {row['close']}"
        for idx, row in df.iterrows()
    ]
    regions_to_plot = []
    for tid, trade in st.session_state['trades'].items():
        if trade.get('show', True):
            for region in trade['regions']:
                if region.get('show', True):
                    regions_to_plot.append(region)
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
        margin=dict(l=0, r=0, t=0, b=0),
        height=chart_height,
        width=None,
        showlegend=False,
        plot_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
        paper_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
        font_color="#f5f5f5" if st.session_state['theme'] == "dark" else "#202020"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Table Functions ---
def trade_table_rows():
    out = []
    for tid, trade in st.session_state['trades'].items():
        entry, entry_idx, exit, exit_idx = "", "", "", ""
        if trade['regions']:
            entry = trade['regions'][0]['start_time'][:10]
            entry_idx = trade['regions'][0]['start_idx']
            exit = trade['regions'][-1]['end_time'][:10]
            exit_idx = trade['regions'][-1]['end_idx']
        out.append({
            "Trade #": tid,
            "Trade Name": trade['name'],
            "Entry Date": entry,
            "Entry Candle": entry_idx,
            "Exit Date": exit,
            "Exit Candle": exit_idx,
            "Visible": trade.get("show", True),
        })
    return out

def region_table_rows(trade):
    out = []
    for idx, region in enumerate(trade["regions"]):
        out.append({
            "Region #": idx + 1,
            "Category": region["category"],
            "Start Date": region["start_time"][:10],
            "Start Candle": region["start_idx"],
            "End Date": region["end_time"][:10],
            "End Candle": region["end_idx"],
            "Feature 1": region.get("feature1", ""),
            "Feature 2": region.get("feature2", ""),
            "Visible": region.get("show", True),
        })
    return out

# --- TRADES TABLE ---
trade_rows = trade_table_rows()
st.markdown(
    "<div class='minimal-table'><table width='100%'><tr>"
    "<th>Trade #</th><th>Name</th><th>Entry Date</th><th>Entry Candle</th>"
    "<th>Exit Date</th><th>Exit Candle</th><th></th><th></th><th></th></tr>",
    unsafe_allow_html=True
)
if trade_rows:
    for tr in trade_rows:
        tid = tr["Trade #"]
        vis = tr["Visible"]
        st.markdown(
            f"<tr>"
            f"<td>{tid}</td>"
            f"<td>{tr['Trade Name']}</td>"
            f"<td>{tr['Entry Date']}</td>"
            f"<td>{tr['Entry Candle']}</td>"
            f"<td>{tr['Exit Date']}</td>"
            f"<td>{tr['Exit Candle']}</td>"
            f"<td style='padding:0 4px 0 0'><span style='cursor:pointer;font-size:20px;'>{get_eye(vis)}</span></td>"
            f"<td style='padding:0 4px 0 0'><span style='cursor:pointer;font-size:18px;'>✏️</span></td>"
            f"<td style='padding:0 2px 0 0'><span style='cursor:pointer;font-size:20px;'>−</span></td>"
            f"</tr>",
            unsafe_allow_html=True
        )
# Always an empty row with plus at right for adding
st.markdown(
    "<tr>"
    "<td></td><td></td><td></td><td></td><td></td><td></td>"
    "<td></td><td></td><td style='padding:0 2px 0 0'><span style='cursor:pointer;font-size:20px;'>+</span></td>"
    "</tr></table></div>", unsafe_allow_html=True
)

# --- REGIONS TABLE ---
selected_trade = st.session_state.get('selected_trade_id')
trade = st.session_state['trades'].get(selected_trade) if selected_trade else None
region_rows = region_table_rows(trade) if trade else []

st.markdown(
    "<div class='minimal-table'><table width='100%'><tr>"
    "<th>Region #</th><th>Category</th><th>Start Date</th><th>Start Candle</th>"
    "<th>End Date</th><th>End Candle</th><th>Feature 1</th><th>Feature 2</th>"
    "<th></th><th></th><th></th></tr>",
    unsafe_allow_html=True
)
if region_rows:
    for idx, rr in enumerate(region_rows):
        vis = rr["Visible"]
        st.markdown(
            f"<tr>"
            f"<td>{rr['Region #']}</td>"
            f"<td>{rr['Category']}</td>"
            f"<td>{rr['Start Date']}</td>"
            f"<td>{rr['Start Candle']}</td>"
            f"<td>{rr['End Date']}</td>"
            f"<td>{rr['End Candle']}</td>"
            f"<td>{rr['Feature 1']}</td>"
            f"<td>{rr['Feature 2']}</td>"
            f"<td style='padding:0 4px 0 0'><span style='cursor:pointer;font-size:20px;'>{get_eye(vis)}</span></td>"
            f"<td style='padding:0 4px 0 0'><span style='cursor:pointer;font-size:18px;'>✏️</span></td>"
            f"<td style='padding:0 2px 0 0'><span style='cursor:pointer;font-size:20px;'>−</span></td>"
            f"</tr>",
            unsafe_allow_html=True
        )
st.markdown(
    "<tr>"
    "<td></td><td></td><td></td><td></td><td></td><td></td>"
    "<td></td><td></td><td></td><td></td>"
    "<td style='padding:0 2px 0 0'><span style='cursor:pointer;font-size:20px;'>+</span></td>"
    "</tr></table></div>", unsafe_allow_html=True
)
