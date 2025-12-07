import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

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
        pos = nx.spring_layout(subgraph)

        plt.figure(figsize=(8, 8))

        # Draw edges first
        edge_colors = []
        edge_widths = []
        for u, v, data in subgraph.edges(data=True):
            if data.get("original_member"):
                edge_colors.append("gold")
                edge_widths.append(3.0)  # bold
            else:
                edge_colors.append("gray")
                edge_widths.append(1.5)

        nx.draw_networkx_edges(
            subgraph, pos,
            edge_color=edge_colors,
            width=edge_widths
        )

        # Draw nodes
        nx.draw_networkx_nodes(
            subgraph, pos,
            node_color=[
                "lightblue" if G.nodes[n].get("type") == "Band" else
                "gold" if G.nodes[n].get("original_member") == "YES" else
                "lightgreen"
                for n in subgraph.nodes
            ],
            node_size=1500
        )

        # Draw labels
        nx.draw_networkx_labels(subgraph, pos, font_size=10)

        # Remove outer box/axes
        plt.axis("off")

        st.pyplot(plt)
    else:
        st.warning("Name not found in dataset.")






