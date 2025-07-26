import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# -- Data Loading --
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    return df

df = load_data()
max_idx = len(df) - 1

st.set_page_config(layout="wide")

# -- Session State for Regions --
if 'regions' not in st.session_state:
    st.session_state['regions'] = []

if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1

if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None

# -- Sidebar Controls for Region Marking --
# --- Sidebar Controls for Region Marking ---
st.sidebar.header("Region Tools")

# Candle info on hover is already provided by Plotly tooltips.

st.sidebar.markdown("**To select a region:**")
st.sidebar.markdown("""
- Hover on the chart to find the desired candle (index/time is shown in tooltip).
- Enter the start and end candle **index** or **timestamp** below.
- All other controls/annotations work as before.
""")

# Manual entry for start/end (index-based, can add timestamp-based if you wish)
start_idx = st.sidebar.number_input("Start Candle Index", min_value=0, max_value=max_idx, value=st.session_state.get('start_idx', 10), step=1, key="start_idx_input")
end_idx = st.sidebar.number_input("End Candle Index", min_value=start_idx+1, max_value=max_idx, value=st.session_state.get('end_idx', 20), step=1, key="end_idx_input")

# Update session state
st.session_state['start_idx'] = start_idx
st.session_state['end_idx'] = end_idx

start_row = df.loc[start_idx]
end_row = df.loc[end_idx]
region_size = end_idx - start_idx + 1

st.sidebar.markdown("---")
st.sidebar.subheader("Region Info")
st.sidebar.write(f"**Start Marker:** idx {start_idx}, {start_row['time']}, price {start_row['close']}")
st.sidebar.write(f"**End Marker:** idx {end_idx}, {end_row['time']}, price {end_row['close']}")
st.sidebar.write(f"**Region Size:** {region_size} candles")


# Marker controls
if 'start_idx' not in st.session_state or st.session_state['start_idx'] >= max_idx:
    st.session_state['start_idx'] = 10
if 'end_idx' not in st.session_state or st.session_state['end_idx'] >= max_idx:
    st.session_state['end_idx'] = 20

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

start_row = df.loc[st.session_state['start_idx']]
end_row = df.loc[st.session_state['end_idx']]
region_size = st.session_state['end_idx'] - st.session_state['start_idx'] + 1

# -- Region Annotation Controls --
st.sidebar.markdown("---")
st.sidebar.subheader("Annotate Region")

category = st.sidebar.selectbox("Category", [
    "Bullish Run-Up", "Bearish Run-Down", "Entry Region"
])

trade_id_options = ["New Trade"] + sorted(set([r['trade_id'] for r in st.session_state['regions'] if r['trade_id'] is not None]))
trade_id_sel = st.sidebar.selectbox("Trade Group", trade_id_options)

if trade_id_sel == "New Trade":
    trade_id = st.session_state['trade_id_counter']
else:
    trade_id = int(trade_id_sel)

key_price = st.sidebar.number_input(
    "Key Price (Target/Stop/Entry)", value=float(end_row['close']), step=0.01, format="%.2f"
)
tags = st.sidebar.text_input("Tags (comma-separated)")
notes = st.sidebar.text_area("Notes")

# -- Save Region Button --
if st.sidebar.button("Save Region"):
    region = {
        'region_id': len(st.session_state['regions']) + 1,
        'trade_id': trade_id,
        'category': category,
        'key_price': key_price,
        'tags': tags,
        'notes': notes,
        'symbol': "AMD",  # Set this dynamically for different charts if needed
        'interval': "1D", # Ditto, or get from user input if needed
        'start_idx': st.session_state['start_idx'],
        'end_idx': st.session_state['end_idx'],
        'start_time': df.loc[st.session_state['start_idx'], 'time'],
        'end_time': df.loc[st.session_state['end_idx'], 'time'],
        'color': {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}[category],
        'events': []
    }
    st.session_state['regions'].append(region)
    if trade_id_sel == "New Trade":
        st.session_state['trade_id_counter'] += 1
    st.success(f"Region saved to Trade {trade_id}")

# -- Trade Region Table/Selection --
st.sidebar.markdown("---")
st.sidebar.subheader("Trades and Regions")

selected_trade = st.sidebar.selectbox(
    "View Trade", ["All"] + sorted(set([str(r['trade_id']) for r in st.session_state['regions']]))
)
if selected_trade == "All":
    regions_to_plot = st.session_state['regions']
else:
    regions_to_plot = [r for r in st.session_state['regions'] if str(r['trade_id']) == selected_trade]

# -- Main Chart with Color Coding --
st.title("Interactive Stock Trade Region Annotator")

fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
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

st.info("Use the sidebar to annotate regions and assign them to trades. Trade regions are highlighted by type (green, red, blue).")

# -- Region Table Display and Delete Button --
st.markdown("### Annotated Regions")
region_df = pd.DataFrame(st.session_state['regions'])

if not region_df.empty:
    for i, region in region_df.iterrows():
        cols = st.columns([6, 1])
        with cols[0]:
            st.write(
                f"**Region {region['region_id']}** (Trade {region['trade_id']}): "
                f"{region['category']} [{region['start_time']} to {region['end_time']}] "
                f"Key Price: {region['key_price']}, Tags: {region['tags']}"
            )
        with cols[1]:
            if st.button(f"Delete {region['region_id']}", key=f"del_{region['region_id']}"):
                st.session_state['regions'] = [r for r in st.session_state['regions'] if r['region_id'] != region['region_id']]
                st.experimental_rerun()
    st.write(region_df.drop(columns=['events', 'color']))
else:
    st.info("No regions have been annotated yet.")
