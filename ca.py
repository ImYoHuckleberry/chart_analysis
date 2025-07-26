import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Load and cache data
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    return df

df = load_data()
max_idx = len(df) - 1

st.set_page_config(layout="wide")

# Sidebar: marker controls
st.sidebar.header("Region Tools")

if 'start_idx' not in st.session_state or st.session_state['start_idx'] >= max_idx:
    st.session_state['start_idx'] = 10
if 'end_idx' not in st.session_state or st.session_state['end_idx'] >= max_idx:
    st.session_state['end_idx'] = 20

# Fine control for markers (start)
st.sidebar.write("**Start Marker Control**")
col1, col2, col3 = st.sidebar.columns([1, 3, 1])
with col1:
    if st.button("−", key="start_dec"):
        st.session_state['start_idx'] = max(0, st.session_state['start_idx'] - 1)
with col2:
    st.session_state['start_idx'] = st.slider(
        "", min_value=0, max_value=st.session_state['end_idx'] - 1,
        value=st.session_state['start_idx'], step=1, key="start_slider"
    )
with col3:
    if st.button("+", key="start_inc"):
        st.session_state['start_idx'] = min(st.session_state['end_idx'] - 1, st.session_state['start_idx'] + 1)

# Fine control for markers (end)
st.sidebar.write("**End Marker Control**")
col1, col2, col3 = st.sidebar.columns([1, 3, 1])
with col1:
    if st.button("−", key="end_dec"):
        st.session_state['end_idx'] = max(st.session_state['start_idx'] + 1, st.session_state['end_idx'] - 1)
with col2:
    st.session_state['end_idx'] = st.slider(
        "", min_value=st.session_state['start_idx'] + 1, max_value=max_idx,
        value=st.session_state['end_idx'], step=1, key="end_slider"
    )
with col3:
    if st.button("+", key="end_inc"):
        st.session_state['end_idx'] = min(max_idx, st.session_state['end_idx'] + 1)

# Marker info display
start_row = df.loc[st.session_state['start_idx']]
end_row = df.loc[st.session_state['end_idx']]
region_size = st.session_state['end_idx'] - st.session_state['start_idx'] + 1

st.sidebar.markdown("---")
st.sidebar.subheader("Region Info")
st.sidebar.write(f"**Start Marker:** idx {st.session_state['start_idx']}, {start_row['time']}, price {start_row['close']}")
st.sidebar.write(f"**End Marker:** idx {st.session_state['end_idx']}, {end_row['time']}, price {end_row['close']}")
st.sidebar.write(f"**Region Size:** {region_size} candles")

# --- Handle axis range for persistent zoom ---
if 'xaxis_range' not in st.session_state:
    st.session_state['xaxis_range'] = None
if 'yaxis_range' not in st.session_state:
    st.session_state['yaxis_range'] = None

# Create Plotly figure
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

# If an axis range is stored, apply it
if st.session_state['xaxis_range']:
    fig.update_xaxes(range=st.session_state['xaxis_range'])
if st.session_state['yaxis_range']:
    fig.update_yaxes(range=st.session_state['yaxis_range'])

fig.update_layout(
    xaxis_rangeslider_visible=False,
    dragmode="zoom",
    margin=dict(l=20, r=20, t=20, b=20),
    height=600,
    showlegend=False
)

# Show chart, capture zoom/pan state
plotly_events = st.plotly_chart(fig, use_container_width=True, key="main_chart", 
    config={"displayModeBar": True, "scrollZoom": True}, 
    on_change=None,  # prevents rerun when zooming
    )
relayout_data = st.session_state.get("plotly_relayout_data", None)

# Use Plotly events to capture zoom/pan
# (Streamlit 1.17+ supports returning relayoutData from st.plotly_chart)
relayout_data = st.get_plotly_events("main_chart", override_height=600, override_width=None, key="main_plotly_events")
if relayout_data:
    for d in relayout_data:
        if "xaxis.range[0]" in d and "xaxis.range[1]" in d:
            st.session_state['xaxis_range'] = [d["xaxis.range[0]"], d["xaxis.range[1]"]]
        if "yaxis.range[0]" in d and "yaxis.range[1]" in d:
            st.session_state['yaxis_range'] = [d["yaxis.range[0]"], d["yaxis.range[1]"]]

st.info("Zoom and pan using your mouse. The current view will remain when you move the region markers.")

