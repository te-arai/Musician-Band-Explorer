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

# Update session_state if user typed something
if manual_query:
    st.session_state["query"] = manual_query.strip()

# Capture clicked node from JS
clicked_node = streamlit_js_eval(js_expressions="window.clickedNode", key="clicked")
if clicked_node:
    st.session_state["query"] = clicked_node.strip()

query = st.session_state["query"]

if query:
    lookup = {str(name).lower(): str(name) for name in G.nodes}
    if query.lower() in lookup:
        actual_name = lookup[query.lower()]
        nodes_within_radius = [
            n for n, dist in nx.single_source_shortest_path_length(G, actual_name).items()
            if dist <= radius
        ]

        st.write(f"Connections within {radius} hops of {actual_name}:")

        if filter_originals:
            filtered_nodes = [
                n for n in nodes_within_radius
                if G.nodes[n].get("original_member") == "YES" or G.nodes[n].get("type") == "Band"
            ]
        else:
            filtered_nodes = nodes_within_radius

        subgraph = G.subgraph(filtered_nodes)

        if theme_choice == "White":
            bg_color, font_color = "white", "black"
            band_color, original_color, musician_color = "#1f77b4", "#ff7f0e", "#2ca02c"
            edge_normal, edge_original = "#888888", "#ff7f0e"
        else:
            bg_color, font_color = "black", "white"
            band_color, original_color, musician_color = "#6baed6", "#ffd700", "#98fb98"
            edge_normal, edge_original = "#aaaaaa", "#ffd700"

        net = Network(height="700px", width="100%", bgcolor=bg_color, font_color=font_color)
        net.force_atlas_2based()

        for node, data in subgraph.nodes(data=True):
            if data.get("type") == "Band":
                color = band_color
            elif data.get("original_member") == "YES":
                color = original_color
            else:
                color = musician_color
            net.add_node(node, label=node, color=color)

        for u, v, data in subgraph.edges(data=True):
            color = edge_original if data.get("original_member") else edge_normal
            width = 3 if data.get("original_member") else 1.5
            net.add_edge(u, v, color=color, width=width)

        html = net.generate_html(notebook=False)

        # Inject JS to capture clicks
        click_js = """
        <script type="text/javascript">
          window.addEventListener("load", function() {
            if (window.network) {
              window.network.on("click", function(params) {
                if (params.nodes.length > 0) {
                  let nodeId = params.nodes[0];
                  window.clickedNode = nodeId;
                  console.log("Clicked node:", nodeId);
                }
              });
            }
          });
        </script>
        """

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

        wrapped_html = f"{css_reset}{html}{click_js}"
        components.html(wrapped_html, height=750, scrolling=True)

    else:
        st.warning("Name not found in dataset.")
