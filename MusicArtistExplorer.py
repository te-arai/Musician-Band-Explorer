import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# --- Load your dataset ---
elements = pd.read_excel("ArtistsBands.xlsx", sheet_name="Elements")
connections = pd.read_excel("ArtistsBands.xlsx", sheet_name="Connections")

# --- Build the undirected graph ---
G = nx.Graph()

# Add nodes (musicians and bands)
for _, row in elements.iterrows():
    label = str(row["Label"]).strip()
    node_type = row.get("Type", "Unknown")
    if label not in G.nodes:  # avoid duplicates
        G.add_node(label, type=node_type, original_member="NO")

# Add edges (connections between musicians and bands)
for _, row in connections.iterrows():
    from_node = str(row["From"]).strip()
    to_node = str(row["To"]).strip()

    # Ensure nodes exist even if missing from Elements
    if from_node not in G.nodes:
        G.add_node(from_node, type="Unknown", original_member="NO")
    if to_node not in G.nodes:
        G.add_node(to_node, type="Unknown", original_member="NO")

    is_original = str(row.get("Original Member", "NO")).strip().upper() == "YES"

    G.add_edge(from_node, to_node, original_member=is_original)

    # Tag whichever side is a musician
    if is_original:
        if G.nodes[from_node].get("type") == "Musician":
            G.nodes[from_node]["original_member"] = "YES"
        if G.nodes[to_node].get("type") == "Musician":
            G.nodes[to_node]["original_member"] = "YES"

# --- Streamlit UI ---
st.title("🎶 Musician ↔ Band Explorer")

# Sidebar controls
st.sidebar.header("Search Options")
query = st.sidebar.text_input("Enter a musician or band name:")
radius = st.sidebar.slider("Connection depth (hops)", 1, 3, 2)

# Filter: Show only Original Members (default = show all nodes)
filter_originals = st.sidebar.checkbox("Only Original Members", value=False)

# Sidebar legend
st.sidebar.markdown("### Legend")
st.sidebar.markdown("- 🟦 **Band
