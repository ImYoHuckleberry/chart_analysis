import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# 1. Load data with caching to prevent reload
@st.cache_data
def load_data():
    # Change path as needed
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    return df

df = load_data()

st.set_page_config(layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Region Tools")

# Initialize marker positions if not already set
if 'start_idx' not in st.session_state or st.session_state['start_idx'] >= len(df):
    st.session_state['start_idx'] = 10
if 'end_idx' not in st.session_state or st.session_state['end_idx'] >= len(df):
    st.session_state['end_idx'] = 20

# Responsive sliders for start and end marker
st.sidebar.write("**Adjust Region Markers**")
st.session_state['start_idx'] = st.sidebar.slider(
    "Start Marker", min_value=0, max_value=len(df)-2,
    value=st.session_state['start_idx'], step=1
)
st.session_state['end_idx'] = st.sidebar.slider(
    "End Marker", min_value=st.session_state['start_idx']+1, max_value=len(df)-1,
    value=st.session_state['end_idx'], step=1
)

# --- Marker Info Display ---
start_row = df.loc[st.session_state['start_idx']]
end_row = df.loc[st.session_state['end_idx']]
region_size = st.session_state['end_idx'] - st.session_state['start_idx'] + 1

st.sidebar.markdown("---")
st.sidebar.subheader("Region Info")
st.sidebar.write(f"**Start Marker:** idx {st.session_state['start_idx']}, {start_row['time']}, price {start_row['close']}")
st.sidebar.write(f"**End Marker:** idx {st.session_state['end_idx']}, {end_row['time']}, price {end_row['close']}")
st.sidebar.write(f"**Region Size:** {region_size} candles")

# --- Main Chart ---
st.title("Interactive Stock Region Selector (Enhanced)")
fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Candles"
)])

# Highlight selected region
fig.add_vrect(
    x0=start_row['time'],
    x1=end_row['time'],
    fillcolor="LightSalmon", opacity=0.3,
    layer="below", line_width=0,
)

# Add marker lines
fig.add_vline(x=start_row['time'], line_width=2, line_color="green")
fig.add_vline(x=end_row['time'], line_width=2, line_color="red")

fig.update_layout(
    xaxis_rangeslider_visible=False,
    dragmode="zoom",      # enable mouse wheel zoom/pan
    margin=dict(l=20, r=20, t=20, b=20),
    height=600,
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

st.info("Zoom and pan using your mouse. Use the sidebar to adjust region markers and view region info.")

# Add more sidebar controls or features as needed (region metadata, saving, etc.)

