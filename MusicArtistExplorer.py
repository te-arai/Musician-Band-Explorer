import streamlit as st
import pandas as pd
import networkx as nx
from visjs_network_component import visjs_network  # our new component

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

# --- UI ---
st.title("🎶 Musician ↔ Band Explorer")

if "query" not in st.session_state:
    st.session_state["query"] = ""

manual_query = st.sidebar.text_input("Enter a musician or band name:", value=st.session_state["query"])
radius = st.sidebar.slider("Connection depth (hops)", 1, 3, 2)
filter_originals = st.sidebar.checkbox("Only Original Members", value=False)
theme_choice = st.sidebar.selectbox("Background Theme", ["White", "Black"])

if manual_query:
    st.session_state["query"] = manual_query.strip()

query = st.session_state["query"]

if query:
    lookup = {str(name).lower(): str(name) for name in G.nodes}
    if query.lower() in lookup:
        actual_name = lookup[query.lower()]
        nodes_within_radius = [
            n for n, dist in nx.single_source_shortest_path_length(G, actual_name).items()
            if dist <= radius
        ]

        if filter_originals:
            filtered_nodes = [
                n for n in nodes_within_radius
                if G.nodes[n].get("original_member") == "YES" or G.nodes[n].get("type") == "Band"
            ]
        else:
            filtered_nodes = nodes_within_radius

        subgraph = G.subgraph(filtered_nodes)

        # Build node/edge lists for component
        nodes = []
        edges = []
        for node, data in subgraph.nodes(data=True):
            if data.get("type") == "Band":
                color = "#1f77b4" if theme_choice == "White" else "#6baed6"
            elif data.get("original_member") == "YES":
                color = "#ff7f0e" if theme_choice == "White" else "#ffd700"
            else:
                color = "#2ca02c" if theme_choice == "White" else "#98fb98"
            nodes.append({"id": node, "label": node, "color": color})

        for u, v, data in subgraph.edges(data=True):
            color = "#ff7f0e" if (theme_choice == "White" and data.get("original_member")) else \
                    "#ffd700" if (theme_choice == "Black" and data.get("original_member")) else \
                    "#888888" if theme_choice == "White" else "#aaaaaa"
            width = 3 if data.get("original_member") else 1.5
            edges.append({"from": u, "to": v, "color": color, "width": width})

        # Call the component
        clicked_node = visjs_network(nodes, edges, key="network")

        if clicked_node and clicked_node != st.session_state["query"]:
            st.session_state["query"] = clicked_node
            st.experimental_rerun()
    else:
        st.warning("Name not found in dataset.")
else:
    st.info("Type a name in the sidebar or click a node to start drilling down.")
