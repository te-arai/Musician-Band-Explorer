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
    G.add_node(label, type=node_type)

# Add edges (connections between musicians and bands)
for _, row in connections.iterrows():
    G.add_edge(row["From"], row["To"])

# --- Streamlit UI ---
st.title("🎶 Musician ↔ Band Explorer")

query = st.text_input("Enter a musician or band name:")

if query:
    query = query.strip()  # remove extra spaces

    # Build a lookup dictionary for case-insensitive search
    lookup = {str(name).lower(): str(name) for name in G.nodes}

    if query.lower() in lookup:
        actual_name = lookup[query.lower()]  # get the correctly cased name

        radius = st.slider("Connection depth (hops)", 1, 3, 2)
        nodes_within_radius = [
            n for n, dist in nx.single_source_shortest_path_length(G, actual_name).items()
            if dist <= radius
        ]

        st.write(f"Connections within {radius} hops of {actual_name}:")
        st.write(nodes_within_radius)

        subgraph = G.subgraph(nodes_within_radius)
        pos = nx.spring_layout(subgraph)

        plt.figure(figsize=(8, 8))
        nx.draw(
            subgraph, pos,
            with_labels=True,
            node_color=[
                "red" if n == actual_name else
                "lightblue" if G.nodes[n].get("type", "Unknown") == "Band" else "lightgreen"
                for n in subgraph.nodes
            ],
            node_size=1500,
            font_size=10
        )
        st.pyplot(plt)
    else:
        st.warning("Name not found in dataset.")
