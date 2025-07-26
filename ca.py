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

# --- SIDEBAR: Mode Selection ---
st.sidebar.header("Region/Trade Actions")
mode = st.sidebar.radio("Select Action Mode:", [
    "Create Region",
    "Modify Region",
    "Add Region to Trade",
    "Edit Trade"
], index=0)

# Show quick instructions
st.sidebar.info("""
**Instructions:**  
- Hover over chart candles to see index and timestamp.
- Use the candle index to set region start/end below.
- Complete annotation fields and save.
- To delete a region, use the button below the chart.
""")

# --- Sidebar Controls for Region Marking ---
if mode == "Create Region" or mode == "Add Region to Trade":
    st.sidebar.subheader("Define Region by Candle Index")
    start_idx = st.sidebar.number_input(
        "Start Candle Index", min_value=0, max_value=max_idx,
        value=st.session_state.get('start_idx', 10), step=1, key="start_idx_input"
    )
    end_idx = st.sidebar.number_input(
        "End Candle Index", min_value=start_idx + 1, max_value=max_idx,
        value=st.session_state.get('end_idx', 20), step=1, key="end_idx_input"
    )
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
            'symbol': "AMD",  # Set dynamically for different charts if needed
            'interval': "1D", # Ditto, or get from user input if needed
            'start_idx': start_idx,
            'end_idx': end_idx,
            'start_time': df.loc[start_idx, 'time'],
            'end_time': df.loc[end_idx, 'time'],
            'color': {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}[category],
            'events': []
        }
        st.session_state['regions'].append(region)
        if trade_id_sel == "New Trade":
            st.session_state['trade_id_counter'] += 1
        st.success(f"Region saved to Trade {trade_id}")

# --- Main Chart with Color Coding ---
st.title("Interactive Stock Trade Region Annotator")

selected_trade = st.sidebar.selectbox(
    "View Trade Regions", ["All"] + sorted(set([str(r['trade_id']) for r in st.session_state['regions']]))
)
if selected_trade == "All":
    regions_to_plot = st.session_state['regions']
else:
    regions_to_plot = [r for r in st.session_state['regions'] if str(r['trade_id']) == selected_trade]

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
