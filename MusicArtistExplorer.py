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

# Theme toggle
theme_choice = st.sidebar.selectbox("Background Theme", ["White", "Black"])

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

        # --- Theme-specific palettes ---
        if theme_choice == "White":
            bg_color = "white"
            font_color = "black"
            band_color = "#1f77b4"        # medium blue
            original_color = "#ff7f0e"    # orange/gold
            musician_color = "#2ca02c"    # green
            edge_normal = "#888888"       # medium gray
            edge_original = "#ff7f0e"     # orange
        else:  # Black theme
            bg_color = "black"
            font_color = "white"
            band_color = "#6baed6"        # light blue
            original_color = "#ffd700"    # bright gold
            musician_color = "#98fb98"    # pale green
            edge_normal = "#aaaaaa"       # light gray
            edge_original = "#ffd700"     # gold

        # --- PyVis interactive graph ---
        net = Network(height="700px", width="100%", bgcolor=bg_color, font_color=font_color)
        net.force_atlas_2based()  # physics layout

        # Add nodes with theme colors
        for node, data in subgraph.nodes(data=True):
            if data.get("type") == "Band":
                color = band_color
            elif data.get("original_member") == "YES":
                color = original_color
            else:
                color = musician_color
            net.add_node(node, label=node, color=color)

        # Add edges with theme colors
        for u, v, data in subgraph.edges(data=True):
            color = edge_original if data.get("original_member") else edge_normal
            width = 3 if data.get("original_member") else 1.5
            net.add_edge(u, v, color=color, width=width)

        # Generate HTML
        html = net.generate_html(notebook=False)

        # --- CSS reset based on theme ---
        css_reset = f"""
        <style>
          html, body {{
            background: {bg_color} !important;
            color: {font_color} !important;
          }}
          #mynetwork {{
            background: {bg_color} !important;
          }}
          #mynetwork canvas {{
            background: {bg_color} !important;
          }}
        </style>
        """

        wrapped_html = f"{css_reset}{html}"

        # Embed in Streamlit
        components.html(wrapped_html, height=750, scrolling=True)

    else:
        st.warning("Name not found in dataset.")
