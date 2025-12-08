# Generate HTML
html = net.generate_html(notebook=False)

# --- CSS reset based on theme ---
body_color = "white" if theme_choice == "White" else "black"
text_color = "black" if theme_choice == "White" else "white"

css_reset = f"""
<style>
  html, body {{
    background: {body_color} !important;
    color: {text_color} !important;
  }}
  #mynetwork {{
    background: {body_color} !important;
  }}
  #mynetwork canvas {{
    background: {body_color} !important;
  }}
</style>
"""

# Wrap the HTML with the CSS reset
wrapped_html = f"{css_reset}{html}"

# Embed in Streamlit
components.html(wrapped_html, height=750, scrolling=True)
