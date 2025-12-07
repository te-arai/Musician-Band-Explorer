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
st.sidebar.markdown("- 🟦 **Band**")
st.sidebar.markdown("- 🟨 **Original Member**")
st.sidebar.markdown("- 🟩 **Other Musician**")
st.sidebar.markdown("- **Gray line**: Connection")
st.sidebar.markdown("- **Gold line**: Original Member Connection")

if query:
    query = query.strip()

    # Case-insensitive lookup
    lookup = {str(name).lower(): str(name) for name in G.nodes}

    if query.lower() in lookup:
        actual_name = lookup[query.lower()]

        nodes_within_radius = [
            n for n, dist in nx.single_source_shortest_path_length(G, actual_name).items()
            if dist <= radius
        ]

        st.write(f"Connections within {radius} hops of {actual_name}:")

        # --- Apply filter ---
        if filter_originals:
            filtered_nodes = [
                n for n in nodes_within_radius
                if G.nodes[n].get("original_member") == "YES" or G.nodes[n].get("type") == "Band"
            ]
        else:
            filtered_nodes = nodes_within_radius

        subgraph = G.subgraph(filtered_nodes)

        # --- PyVis interactive graph ---
        net = Network(height="700px", width="100%", bgcolor="white", font_color="black")
        net.force_atlas_2based()  # physics layout

        # Add nodes with colors
        for node, data in subgraph.nodes(data=True):
            color = (
                "lightblue" if data.get("type") == "Band" else
                "gold" if data.get("original_member") == "YES" else
                "lightgreen"
            )
            net.add_node(node, label=node, color=color)

        # Add edges with colors/widths
        for u, v, data in subgraph.edges(data=True):
            color = "gold" if data.get("original_member") else "gray"
            width = 3 if data.get("original_member") else 1.5
            net.add_edge(u, v, color=color, width=width)

        # Optional: style labels and default edge color via vis.js options
        net.set_options("""
        var options = {
          nodes: { font: { color: "black", size: 16 } },
          edges: { color: { color: "gray" } },
          physics: { stabilization: true }
        }
        """)

        # Generate HTML
        html = net.generate_html
