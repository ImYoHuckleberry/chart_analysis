import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Load sample data (use a subset for demonstration)
df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
df = df.iloc[-300:].reset_index(drop=True)  # last 300 candles for performance

st.title("Interactive Stock Region Selector")

# Set up state for start/end markers
if 'start_idx' not in st.session_state:
    st.session_state['start_idx'] = 10
if 'end_idx' not in st.session_state:
    st.session_state['end_idx'] = 20

# Marker selection via sliders or input boxes
st.write("Select region to annotate:")

col1, col2 = st.columns(2)
with col1:
    st.session_state['start_idx'] = st.number_input(
        "Start Candle (index)", min_value=0, max_value=len(df)-1,
        value=st.session_state['start_idx'], step=1, key="start"
    )
with col2:
    st.session_state['end_idx'] = st.number_input(
        "End Candle (index)", min_value=st.session_state['start_idx']+1, max_value=len(df)-1,
        value=st.session_state['end_idx'], step=1, key="end"
    )

start_ts = df.loc[st.session_state['start_idx'], "time"]
end_ts = df.loc[st.session_state['end_idx'], "time"]
st.write(f"**Selected region:** {start_ts} — {end_ts} (indices {st.session_state['start_idx']}–{st.session_state['end_idx']})")

# Plotly candlestick with region highlighted
fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Candles"
)])

# Highlight region
fig.add_vrect(
    x0=df.loc[st.session_state['start_idx'], "time"],
    x1=df.loc[st.session_state['end_idx'], "time"],
    fillcolor="LightSalmon", opacity=0.3,
    layer="below", line_width=0,
)

# Add start/end marker lines
fig.add_vline(x=df.loc[st.session_state['start_idx'], "time"], line_width=2, line_color="green")
fig.add_vline(x=df.loc[st.session_state['end_idx'], "time"], line_width=2, line_color="red")

fig.update_layout(
    xaxis_rangeslider_visible=False,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)
