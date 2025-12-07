import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# --- Load your dataset ---
elements = pd.read_excel("ArtistsBands.xlsx", sheet_name="Elements")
connections = pd.read_excel("ArtistsBands.xlsx", sheet_name="Connections")

# --- Build the graph ---
G = nx.Graph()

# Add nodes (musicians and bands)
for _, row in elements.iterrows():
    label = row["Label"]
    node_type = row.get("Type", "Unknown")
    G.add_node(label, type=node_type, original_member="NO")  # default

# Add edges (connections between musicians and bands)
for _, row in connections.iterrows():
    from_node = row["From"]
    to_node = row["To"]
    G.add_edge(from_node, to_node)

    # If this connection marks the musician as an original member
    if str(row.get("Original Member", "NO")).strip().upper() == "YES":
        # Tag whichever side is a musician
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

# Legend moved to sidebar
st.sidebar.markdown("""
**Legend:**
- 🔴 Red = Selected node
- 🔵 Blue = Band
- 🟡 Gold = Original Member (Musician)
- 🟢 Green = Other Musician
""")

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
        # Commented out list of names for cleaner UI
        # st.write(nodes_within_radius)

        subgraph = G.subgraph(nodes_within_radius)
        pos = nx.spring_layout(subgraph)

        plt.figure(figsize=(8, 8))
        nx.draw(
            subgraph, pos,
            with_labels=True,
            node_color=[
                "red" if n == actual_name else
                "lightblue" if G.nodes[n].get("type") == "Band" else
                "gold" if G.nodes[n].get("original_member") == "YES" else
                "lightgreen"
                for n in subgraph.nodes
            ],
            node_size=1500,
            font_size=10
        )

        st.pyplot(plt)
    else:
        st.warning("Name not found in dataset.")
