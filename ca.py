import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

# --- Data Loading ---
@st.cache_data
def load_data():
    df = pd.read_csv("NASDAQ_AMD, 1D_pp.csv")
    df = df.iloc[-300:].reset_index(drop=True)
    df['candle_idx'] = df.index
    return df

df = load_data()
max_idx = len(df) - 1

st.set_page_config(layout="wide")

# --- Session State for Trades and Regions ---
if 'trades' not in st.session_state:
    st.session_state['trades'] = {}  # {trade_id: {'name': str, 'regions': [region_dict, ...]}}
if 'trade_id_counter' not in st.session_state:
    st.session_state['trade_id_counter'] = 1
if 'selected_trade_id' not in st.session_state:
    st.session_state['selected_trade_id'] = None
if 'edit_region_idx' not in st.session_state:
    st.session_state['edit_region_idx'] = None

def get_trade_options():
    return [(tid, v['name']) for tid, v in st.session_state['trades'].items()]

def region_color(category):
    return {'Bullish Run-Up': "green", 'Bearish Run-Down': "red", 'Entry Region': "blue"}.get(category, 'grey')

# --- SIDEBAR MAIN MODE SELECTION ---
st.sidebar.title("Trade & Region Workflow")
main_mode = st.sidebar.radio("Select an action:", [
    "Create New Trade",
    "Select/Edit Existing Trade"
])

if st.sidebar.checkbox("Show brief instructions"):
    st.sidebar.info("""
    - Hover candles to see **Index** and **Date** for sidebar entry.
    - Use sidebar to manage trades and regions.
    - Index is best for precision; date is optional for convenience.
    """)

# --- CREATE NEW TRADE ---
if main_mode == "Create New Trade":
    st.sidebar.subheader("Create a Trade")
    trade_name = st.sidebar.text_input("Trade Name")
    if st.sidebar.button("Create Trade") and trade_name:
        new_trade_id = st.session_state['trade_id_counter']
        st.session_state['trades'][new_trade_id] = {'name': trade_name, 'regions': []}
        st.session_state['selected_trade_id'] = new_trade_id
        st.session_state['trade_id_counter'] += 1
        st.success(f"Trade '{trade_name}' created. Proceed to region annotation.")
        st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

# --- SELECT OR EDIT EXISTING TRADE ---
elif main_mode == "Select/Edit Existing Trade":
    trade_options = get_trade_options()
    if trade_options:
        tid_list, tnames = zip(*trade_options)
        sel_trade_idx = st.sidebar.selectbox("Select Trade", range(len(trade_options)), format_func=lambda i: f"{tid_list[i]}: {tnames[i]}")
        selected_trade_id = tid_list[sel_trade_idx]
        st.session_state['selected_trade_id'] = selected_trade_id
        trade = st.session_state['trades'][selected_trade_id]
        st.sidebar.markdown(f"**Trade Name:** {trade['name']}")
        region_list = trade['regions']

        # --- REGION WORKFLOW WITHIN SELECTED TRADE ---
        reg_action = st.sidebar.radio("Region Actions:", [
            "Add Region", "Modify Region"
        ], horizontal=True)

        # --- ADD REGION ---
        if reg_action == "Add Region":
            st.sidebar.subheader("Add Region to This Trade")
            sidebar_cols = st.sidebar.columns(2)
            with sidebar_cols[0]:
                start_idx = st.number_input("Start Index", min_value=0, max_value=max_idx, value=10, step=1, key="add_start_idx")
            with sidebar_cols[1]:
                end_idx = st.number_input("End Index", min_value=start_idx + 1, max_value=max_idx, value=20, step=1, key="add_end_idx")

            # Date option for quick jump (optional)
            date_cols = st.sidebar.columns(2)
            with date_cols[0]:
                start_date = st.date_input("Start Date", pd.to_datetime(df.loc[start_idx, 'time']).date(), key="add_start_date")
            with date_cols[1]:
                end_date = st.date_input("End Date", pd.to_datetime(df.loc[end_idx, 'time']).date(), key="add_end_date")
            # If user updates date, adjust index
            if start_date:
                idx_match = df[df['time'].str[:10] == str(start_date)].index
                if not idx_match.empty:
                    start_idx = idx_match[0]
            if end_date:
                idx_match = df[df['time'].str[:10] == str(end_date)].index
                if not idx_match.empty:
                    end_idx = idx_match[-1]

            category = st.sidebar.selectbox("Category", [
                "Bullish Run-Up", "Bearish Run-Down", "Entry Region"
            ], key="add_category")
            key_price = st.sidebar.number_input("Key Price (Target/Stop/Entry)", value=float(df.loc[end_idx, 'close']), step=0.01, format="%.2f", key="add_key_price")
            tags = st.sidebar.text_input("Tags", key="add_tags")
            notes = st.sidebar.text_area("Notes", key="add_notes")
            if st.sidebar.button("Save Region", key="add_save_region"):
                region = {
                    'region_id': len(region_list) + 1,
                    'category': category,
                    'key_price': key_price,
                    'tags': tags,
                    'notes': notes,
                    'symbol': "AMD",
                    'interval': "1D",
                    'start_idx': int(start_idx),
                    'end_idx': int(end_idx),
                    'start_time': df.loc[int(start_idx), 'time'],
                    'end_time': df.loc[int(end_idx), 'time'],
                    'color': region_color(category)
                }
                trade['regions'].append(region)
                st.success("Region added.")
                st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

        # --- MODIFY REGION ---
        elif reg_action == "Modify Region":
            st.sidebar.subheader("Edit a Region")
            if region_list:
                reg_idx = st.sidebar.selectbox(
                    "Select Region", range(len(region_list)),
                    format_func=lambda i: f"{region_list[i]['category']} ({region_list[i]['start_time']} to {region_list[i]['end_time']})"
                )
                region = region_list[reg_idx]
                # Editable fields
                start_idx = st.sidebar.number_input("Start Index", min_value=0, max_value=max_idx, value=region['start_idx'], step=1, key="edit_start_idx")
                end_idx = st.sidebar.number_input("End Index", min_value=start_idx + 1, max_value=max_idx, value=region['end_idx'], step=1, key="edit_end_idx")
                category = st.sidebar.selectbox("Category", [
                    "Bullish Run-Up", "Bearish Run-Down", "Entry Region"
                ], index=["Bullish Run-Up", "Bearish Run-Down", "Entry Region"].index(region['category']), key="edit_category")
                key_price = st.sidebar.number_input("Key Price (Target/Stop/Entry)", value=float(region['key_price']), step=0.01, format="%.2f", key="edit_key_price")
                tags = st.sidebar.text_input("Tags", value=region['tags'], key="edit_tags")
                notes = st.sidebar.text_area("Notes", value=region['notes'], key="edit_notes")
                if st.sidebar.button("Update Region", key="edit_update_region"):
                    region_list[reg_idx] = {
                        **region,
                        'category': category,
                        'key_price': key_price,
                        'tags': tags,
                        'notes': notes,
                        'start_idx': int(start_idx),
                        'end_idx': int(end_idx),
                        'start_time': df.loc[int(start_idx), 'time'],
                        'end_time': df.loc[int(end_idx), 'time'],
                        'color': region_color(category)
                    }
                    st.success("Region updated.")
                    st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
                # Delete region
                if st.sidebar.button("Delete Region", key="edit_delete_region"):
                    region_list.pop(reg_idx)
                    st.success("Region deleted.")
                    st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
            else:
                st.sidebar.info("No regions to edit for this trade.")
    else:
        st.sidebar.info("No trades defined yet. Use 'Create New Trade' first.")

# --- MAIN CHART ---
st.title("Stock Trade Region Annotator")

# Only show relevant regions for selected trade (if any)
regions_to_plot = []
if st.session_state['selected_trade_id'] and st.session_state['selected_trade_id'] in st.session_state['trades']:
    regions_to_plot = st.session_state['trades'][st.session_state['selected_trade_id']]['regions']
elif main_mode == "Create New Trade":
    regions_to_plot = []

fig = go.Figure(data=[go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    customdata=df['candle_idx'],
    hovertemplate=(
        'Index: %{customdata}<br>'
        'Date: %{x}<br>'
        'Open: %{open}<br>'
        'High: %{high}<br>'
        'Low: %{low}<br>'
        'Close: %{close}<br>'
        '<extra></extra>'
    ),
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

# --- REGION TABLE ---
if regions_to_plot:
    st.markdown("### Regions in Current Trade")
    region_table = pd.DataFrame([
        {**r, "start_date": r["start_time"][:10], "end_date": r["end_time"][:10]}
        for r in regions_to_plot
    ])
    st.dataframe(region_table[["region_id", "category", "start_idx", "start_date", "end_idx", "end_date", "key_price", "tags", "notes"]])
else:
    st.info("No regions defined for this trade yet.")
