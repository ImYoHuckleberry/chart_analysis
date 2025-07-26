import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Load data with caching
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    return df

df = load_data()
st.set_page_config(layout="wide")
max_idx = len(df) - 1

# --- SIDEBAR ---
st.sidebar.header("Region Tools")

# Init markers if needed
if 'start_idx' not in st.session_state or st.session_state['start_idx'] >= max_idx:
    st.session_state['start_idx'] = 10
if 'end_idx' not in st.session_state or st.session_state['end_idx'] >= max_idx:
    st.session_state['end_idx'] = 20

# Fine control buttons (Start marker)
st.sidebar.write("**Start Marker Control**")
col1, col2, col3 = st.sidebar.columns([1, 3, 1])
with col1:
    if st.button("−", key="start_dec", help="Move start marker left by 1"):
        st.session_state['start_idx'] = max(0, st.session_state['start_idx'] - 1)
with col2:
    st.session_state['start_idx'] = st.slider(
        "", min_value=0, max_value=st.session_state['end_idx'] - 1,
        value=st.session_state['start_idx'], step=1, key="start_slider"
    )
with col3:
    if st.button("+", key="start_inc", help="Move start marker right by 1"):
        st.session_state['start_idx'] = min(st.session_state['end_idx'] - 1, st.session_state['start_idx'] + 1)

# Fine control buttons (End marker)
st.sidebar.write("**End Marker Control**")
col1, col2, col3 = st.sidebar.columns([1, 3, 1])
with col1:
    if st.button("−", key="end_dec", help="Move end marker left by 1"):
        st.session_state['end_idx'] = max(st.session_state['start_idx'] + 1, st.session_state['end_idx'] - 1)
with col2:
    st.session_state['end_idx'] = st.slider(
        "", min_value=st.session_state['start_idx'] + 1, max_value=max_idx,
        value=st.session_state['end_idx'], step=1, key="end_slider"
    )
with col3:
    if st.button("+", key="end_inc", help="Move end marker right by 1"):
        st.session_state['end_idx'] = min(max_idx, st.session_state['end_idx'] + 1)

# Marker info
start_row = df.loc[st.session_state['start_idx']]
end_row = df.loc[st.session_state['end_idx']]
region_size = st.session_state['end_idx'] - st.session_state['start_idx'] + 1

st.sidebar.markdown("---")
st.sidebar.subheader("Region Info")
st.sidebar.write(f"**Start Marker:** idx {st.session_state['start_idx']}, {start_row['time']}, price {start_row['close']}")
st.sidebar.write(f"**End Marker:** idx {st.session_state['end_idx']}, {end_row['time']}, price {end_row['close']}")
st.sidebar.write(f"**Region Size:** {region_size} candles")

# Chart
st.title("Interactive Stock Region Selector (Enhanced)")
fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Candles"
)])
fig.add_vrect(
    x0=start_row['time'],
    x1=end_row['time'],
    fillcolor="LightSalmon", opacity=0.3,
    layer="below", line_width=0,
)
fig.add_vline(x=start_row['time'], line_width=2, line_color="green")
fig.add_vline(x=end_row['time'], line_width=2, line_color="red")
fig.update_layout(
    xaxis_rangeslider_visible=False,
    dragmode="zoom",
    margin=dict(l=20, r=20, t=20, b=20),
    height=600,
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

st.info("Zoom and pan using your mouse. Use the sidebar to adjust region markers and view region info.")
