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
if 'regions' not in st.session_state:
    st.session_state['regions'] = []
if 'edit_mode' not in st.session_state:
    st.session_state['edit_mode'] = False
if 'edit_idx' not in st.session_state:
    st.session_state['edit_idx'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = "dark"
if 'chart_height_sel' not in st.session_state:
    st.session_state['chart_height_sel'] = "Medium (600px)"

# --- THEME SWITCH (SUN/MOON ICON) ---
def sunmoon_switch():
    toggle = st.button("🌙" if st.session_state['theme'] == "dark" else "☀️", key="theme_toggle", help="Toggle theme")
    if toggle:
        st.session_state['theme'] = "light" if st.session_state['theme'] == "dark" else "dark"
        st.experimental_rerun()
sunmoon_switch()

# --- Theme: Style Inject ---
if st.session_state['theme'] == "dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #171717 !important; color: #f5f5f5 !important; }
        th { background: #232323 !important; color: #fafafa !important; font-size:14px; font-weight:600; border-bottom:1px solid #444;}
        td { background: #232323 !important; color: #d3d3d3 !important; font-size:13px; font-weight:normal;}
        .minimal-table td, .minimal-table th { text-align: center; padding: 6px 6px; border-bottom:1px solid #333;}
        .minimal-table tr:last-child td { border-bottom:0;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #fafafa !important; color: #202020 !important; }
        th { background: #f4f4f4 !important; color: #222 !important; font-size:14px; font-weight:600; border-bottom:1px solid #ddd;}
        td { background: #fff !important; color: #3a3a3a !important; font-size:13px; font-weight:normal;}
        .minimal-table td, .minimal-table th { text-align: center; padding: 6px 6px; border-bottom:1px solid #eee;}
        .minimal-table tr:last-child td { border-bottom:0;}
        </style>
        """, unsafe_allow_html=True)

# --- Chart Height Selection ---
chart_height_map = {
    "Small (400px)": 400,
    "Medium (600px)": 600,
    "Large (900px)": 900,
    "Full Window": 850,
}
chart_height = chart_height_map.get(st.session_state['chart_height_sel'], 600)
st.session_state['chart_height_sel'] = st.selectbox(
    "Chart Height", ["Small (400px)", "Medium (600px)", "Large (900px)", "Full Window"],
    index=["Small (400px)", "Medium (600px)", "Large (900px)", "Full Window"].index(st.session_state['chart_height_sel']), key="chart_height_selbox"
)

# --- SIDEBAR: REGION ENTRY/EDIT ---
st.sidebar.markdown("### Region Editor")
category = st.sidebar.selectbox("Category", ["Bullish Run-Up", "Bearish Run-Down", "Entry Region"], key="cat")
feature1 = st.sidebar.selectbox("Feature 1", ["Order Block", "Gap Up", "Gap Down", "Cumulative Delta Flip", "High Vol on Short Candle"], key="f1")
feature2 = st.sidebar.selectbox("Feature 2", ["None", "Volume Spike", "Trend Break", "Inside Bar"], key="f2")
start_idx = st.sidebar.number_input("Start Candle", min_value=0, max_value=max_idx, value=10, step=1, key="start_idx")
end_idx = st.sidebar.number_input("End Candle", min_value=start_idx + 1, max_value=max_idx, value=20, step=1, key="end_idx")
start_time = df.loc[start_idx, 'time']
end_time = df.loc[end_idx, 'time']
key_price = st.sidebar.number_input("Key Price", value=float(df.loc[end_idx, 'close']), step=0.01, format="%.2f", key="kp")
tags = st.sidebar.text_input("Tags", key="tags")
notes = st.sidebar.text_area("Notes", key="notes")

if st.session_state['edit_mode']:
    if st.sidebar.button("Update Region", key="update_region"):
        st.session_state['regions'][st.session_state['edit_idx']] = {
            "Category": category,
            "Feature 1": feature1,
            "Feature 2": feature2,
            "Start Date": start_time[:10],
            "Start Candle": start_idx,
            "End Date": end_time[:10],
            "End Candle": end_idx,
            "Key Price": key_price,
            "Tags": tags,
            "Notes": notes
        }
        st.session_state['edit_mode'] = False
        st.experimental_rerun()
    if st.sidebar.button("Cancel Edit", key="cancel_edit"):
        st.session_state['edit_mode'] = False
        st.experimental_rerun()
else:
    if st.sidebar.button("Add Region", key="add_region"):
        st.session_state['regions'].append({
            "Category": category,
            "Feature 1": feature1,
            "Feature 2": feature2,
            "Start Date": start_time[:10],
            "Start Candle": start_idx,
            "End Date": end_time[:10],
            "End Candle": end_idx,
            "Key Price": key_price,
            "Tags": tags,
            "Notes": notes
        })
        st.experimental_rerun()

# --- MAIN CHART ---
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
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
for idx, region in enumerate(st.session_state['regions']):
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
    height=chart_height,
    showlegend=False,
    plot_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    paper_bgcolor="#171717" if st.session_state['theme'] == "dark" else "#fff",
    font_color="#f5f5f5" if st.session_state['theme'] == "dark" else "#202020"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABLE BELOW CHART: REGIONS ---
st.markdown("<div class='minimal-table'><table width='100%'><tr>"
    "<th>#</th><th>Category</th><th>Feature 1</th><th>Feature 2</th><th>Start Date</th><th>Start Candle</th>"
    "<th>End Date</th><th>End Candle</th><th>Key Price</th><th>Tags</th><th>Notes</th></tr>",
    unsafe_allow_html=True)
if st.session_state['regions']:
    for idx, region in enumerate(st.session_state['regions']):
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
            f"</tr>",
            unsafe_allow_html=True
        )
else:
    # always show headers even if no data, and one blank row to match Excel
    st.markdown("<tr><td colspan='11' style='color:#aaa;'>&nbsp;</td></tr>", unsafe_allow_html=True)
st.markdown("</table></div>", unsafe_allow_html=True)
