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
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None
if 'show_add_trade' not in st.session_state:
    st.session_state['show_add_trade'] = False
if 'show_add_region' not in st.session_state:
    st.session_state['show_add_region'] = False
if 'theme' not in st.session_state:
    st.session_state['theme'] = "dark"
if 'show_left_sidebar' not in st.session_state:
    st.session_state['show_left_sidebar'] = True
if 'show_right_sidebar' not in st.session_state:
    st.session_state['show_right_sidebar'] = True

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
        .stDataFrame, .css-1v0mbdj, .stTable, .stMarkdown { background: #232323; color: #f5f5f5; }
        th { background: #232323 !important; color: #f5f5f5 !important; }
        td { background: #232323 !important; color: #f5f5f5 !important; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #fafafa !important; color: #202020 !important; }
        .stDataFrame, .css-1v0mbdj, .stTable, .stMarkdown { background: #fff; color: #202020; }
        th { background: #f4f4f4 !important; color: #202020 !important; }
        td { background: #fff !important; color: #202020 !important; }
        </style>
        """, unsafe_allow_html=True)

# --- SIDEBAR: Left (Tools) ---
if st.session_state['show_left_sidebar']:
    with st.sidebar:
        chevron = st.button("«", help="Hide Tools", key="hide_tools_chevron")
        if chevron:
            st.session_state['show_left_sidebar'] = False
            st.experimental_rerun()
        st.markdown("### Tools")
        region_type = st.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="tool_category")
        feature1 = st.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="tool_feature1")
        feature2 = st.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="tool_feature2")
        note = st.text_area("Notes/Observations", key="tool_notes")
        chart_height = st.selectbox("Chart Height", ["Small (400px)", "Medium (600px)", "Large (900px)", "Full Window"], index=1, key="chart_height_sel")
        # Theme toggle
        if st.toggle("Night Mode", value=(st.session_state['theme'] == "dark"), key="theme_toggle"):
            if st.session_state['theme'] != "dark":
                st.session_state['theme'] = "dark"
                st.experimental_rerun()
        else:
            if st.session_state['theme'] != "light":
                st.session_state['theme'] = "light"
                st.experimental_rerun()
else:
    left_edge = st.button("»", help="Show Tools", key="show_tools_chevron")
    if left_edge:
        st.session_state['show_left_sidebar'] = True
        st.experimental_rerun()

# --- SIDEBAR: Right (Directions/Help) ---
if st.session_state['show_right_sidebar']:
    right_style = "position:fixed;right:0;top:0;width:270px;height:100vh;overflow:auto;background:#232323;padding:30px 10px 10px 20px;border-left:2px solid #444;z-index:9999;" if st.session_state['theme'] == "dark" else "position:fixed;right:0;top:0;width:270px;height:100vh;overflow:auto;background:#fff;padding:30px 10px 10px 20px;border-left:2px solid #ddd;z-index:9999;"
    st.markdown(
        f"""
        <div style='{right_style}'>
            <div style='position:absolute;left:12px;top:6px;'><form action=""><button style="border:none;background:transparent;font-size:22px;cursor:pointer;color:#aaa;" name="hide_dir" type="submit">&#8249;</button></form></div>
            <div style='font-size:20px;font-weight:bold;margin-bottom:7px;'>Directions</div>
            <ul style='font-size:15px;'>
            <li>Use <b>+</b> at right of tables to add.</li>
            <li><b>✏️</b> for edit, <b>👁️</b> for visibility.</li>
            <li>Click a trade row to select and view regions.</li>
            <li>Left panel: always annotation tools and chart height.</li>
            <li>Chart: fully resizes, fills available space.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    if "hide_dir" in st.query_params:
        st.session_state['show_right_sidebar'] = False
        st.experimental_rerun()
else:
    right_edge = st.button("›", help="Show Directions", key="show_dir_chevron", disabled=False)
    if right_edge:
        st.session_state['show_right_sidebar'] = True
        st.experimental_rerun()

# --- CHART HEIGHT SELECTION ---
chart_height_map = {
    "Small (400px)": 400,
    "Medium (600px)": 600,
    "Large (900px)": 900,
    "Full Window": int(st.session_state.get('window_height', 700)),
}
chart_height = chart_height_map.get(st.session_state.get("chart_height_sel", "Medium (600px)"), 600)

# --- MAIN CHART AREA ---
main_container_cols = [1, 12, 1] if st.session_state['show_left_sidebar'] and st.session_state['show_right_sidebar'] else ([1, 16] if st.session_state['show_left_sidebar'] or st.session_state['show_right_sidebar'] else [1])
main_col_idx = 1 if len(main_container_cols) > 1 else 0

with st.container():
    cols = st.columns(main_container_cols, gap="small")
    chart_col = cols[main_col_idx]
    with chart_col:
        # Compose list of visible regions for all trades set to "show"
        regions_to_plot = []
        for tid, trade in st.session_state['trades'].items():
            if trade.get('show', True):
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
            margin=dict(l=0, r=0, t=0, b=0),
            height=chart_height,
            width=None,
            showlegend=False,
            plot_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
            paper_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
            font_color="#f5f5f5" if st.session_state['theme'] == "dark" else "#202020"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- TRADES TABLE ---
def trade_table_rows():
    out = []
    for tid, trade in st.session_state['trades'].items():
        entry, exit = "", ""
        if trade['regions']:
            entry = trade['regions'][0]['start_time'][:10]
            exit = trade['regions'][-1]['end_time'][:10]
        out.append({
            "Trade #": tid,
            "Trade Name": trade['name'],
            "Entry Date": entry,
            "Exit Date": exit,
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
            "End Date": region["end_time"][:10],
            "Feature 1": region.get("feature1", ""),
            "Feature 2": region.get("feature2", ""),
            "Visible": region.get("show", True),
        })
    return out

st.write("")  # Spacer only
st.markdown(
    """
    <style>
    .minimal-table thead tr th, .minimal-table tbody tr td { text-align: center; padding: 6px 6px; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Trades Table ---
trade_rows = trade_table_rows()
st.markdown('<div class="minimal-table"><table width="100%"><tr><th>Trade #</th><th>Trade Name</th><th>Entry Date</th><th>Exit Date</th><th></th><th></th><th></th></tr>', unsafe_allow_html=True)
if trade_rows:
    for tr in trade_rows:
        tid = tr["Trade #"]
        vis = tr["Visible"]
        st.markdown(
            f"""<tr>
                <td>{tid}</td>
                <td>{tr['Trade Name']}</td>
                <td>{tr['Entry Date']}</td>
                <td>{tr['Exit Date']}</td>
                <td>
                    <form action="" method="post"><button name="vis_{tid}" style="border:none;background:transparent;font-size:20px;cursor:pointer;">{get_eye(vis)}</button></form>
                </td>
                <td>
                    <form action="" method="post"><button name="edit_{tid}" style="border:none;background:transparent;font-size:18px;cursor:pointer;">✏️</button></form>
                </td>
                <td>
                    <form action="" method="post"><button name="del_{tid}" style="border:none;background:transparent;font-size:20px;cursor:pointer;">+</button></form>
                </td>
            </tr>""", unsafe_allow_html=True)
else:
    st.markdown(
        """<tr><td colspan="7" style="color:#bbb;">(No trades yet)</td></tr>""", unsafe_allow_html=True
    )
st.markdown('</table></div>', unsafe_allow_html=True)

# --- Regions Table (selected trade only) ---
selected_trade = st.session_state.get('selected_trade_id')
trade = st.session_state['trades'].get(selected_trade) if selected_trade else None
region_rows = region_table_rows(trade) if trade else []

st.markdown('<div class="minimal-table"><table width="100%"><tr><th>Region #</th><th>Category</th><th>Start Date</th><th>End Date</th><th>Feature 1</th><th>Feature 2</th><th></th><th></th><th></th></tr>', unsafe_allow_html=True)
if region_rows:
    for idx, rr in enumerate(region_rows):
        vis = rr["Visible"]
        st.markdown(
            f"""<tr>
                <td>{rr['Region #']}</td>
                <td>{rr['Category']}</td>
                <td>{rr['Start Date']}</td>
                <td>{rr['End Date']}</td>
                <td>{rr['Feature 1']}</td>
                <td>{rr['Feature 2']}</td>
                <td>
                    <form action="" method="post"><button name="reg_vis_{idx}" style="border:none;background:transparent;font-size:20px;cursor:pointer;">{get_eye(vis)}</button></form>
                </td>
                <td>
                    <form action="" method="post"><button name="reg_edit_{idx}" style="border:none;background:transparent;font-size:18px;cursor:pointer;">✏️</button></form>
                </td>
                <td>
                    <form action="" method="post"><button name="reg_add_{idx}" style="border:none;background:transparent;font-size:22px;cursor:pointer;">+</button></form>
                </td>
            </tr>""", unsafe_allow_html=True)
else:
    st.markdown(
        """<tr><td colspan="9" style="color:#bbb;">(No regions yet for this trade)</td></tr>""", unsafe_allow_html=True
    )
st.markdown('</table></div>', unsafe_allow_html=True)

# --- Action logic for icons/buttons in table (use st.form or st.session_state for full interactivity in deployment) ---
# Add your Streamlit event logic here based on form postbacks and session_state

# --- End of script ---
