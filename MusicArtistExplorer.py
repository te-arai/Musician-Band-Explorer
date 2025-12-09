import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

# --- Load your dataset ---
elements = pd.read_excel("ArtistsBands.xlsx", sheet_name="Elements")
connections = pd.read_excel("ArtistsBands.xlsx", sheet_name="Connections")

# --- Build the undirected graph ---
G = nx.Graph()

for _, row in elements.iterrows():
    label = str(row["Label"]).strip()
    node_type = row.get("Type", "Unknown")
    if label not in G.nodes:
        G.add_node(label, type=node_type, original_member="NO")

for _, row in connections.iterrows():
    from_node = str(row["From"]).strip()
    to_node = str(row["To"]).strip()

    if from_node not in G.nodes:
        G.add_node(from_node, type="Unknown", original_member="NO")
    if to_node not in G.nodes:
        G.add_node(to_node, type="Unknown", original_member="NO")

    is_original = str(row.get("Original Member", "NO")).strip().upper() == "YES"
    G.add_edge(from_node, to_node, original_member=is_original)

    if is_original:
        if G.nodes[from_node].get("type") == "Musician":
            G.nodes[from_node]["original_member"] = "YES"
        if G.nodes[to_node].get("type") == "Musician":
            G.nodes[to_node]["original_member"] = "YES"

# --- Streamlit UI ---
st.title("🎶 Musician ↔ Band Explorer")

# Initialize session state
if "query" not in st.session_state:
    st.session_state["query"] = ""

st.sidebar.header("Search Options")
manual_query = st.sidebar.text_input("Enter a musician or band name:", value=st.session_state["query"])
radius = st.sidebar.slider("Connection depth (hops)", 1, 3, 2)
filter_originals = st.sidebar.checkbox("Only Original Members", value=False)
theme_choice = st.sidebar.selectbox("Background Theme", ["White", "Black"])

st.sidebar.markdown("### Legend")
st.sidebar.markdown("- 🟦 **Band**")
st.sidebar.markdown("- 🟨 **Original Member**")
st.sidebar.markdown("- 🟩 **Other Musician**")
st.sidebar.markdown("- **Gray line**: Connection")
st.sidebar.markdown("- **Gold line**: Original Member Connection")

# Update query from typing
if manual_query:
    st.session_state["query"] = manual_query.strip()

# Capture clicked node from JS
clicked_node = streamlit_js_eval(js_expressions="window.clickedNode", key="clicked-node")

if clicked_node and clicked_node != st.session_state["query"]:
    st.session_state["query"] = clicked_node.strip()
    st.experimental_rerun()   # <-- force rerun when a new node is clicked

query = st.session_state["query"]

if query:
    lookup = {str(name).lower(): str(name) for
