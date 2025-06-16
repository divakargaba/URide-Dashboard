import streamlit as st

def app():
    st.set_page_config(layout="wide")
    st.markdown("<h1 style='text-align: center; color: black;'>URide Driver and Transit User Routes</h1>", unsafe_allow_html=True)

    # Embed the HTML file directly
    try:
        with open("ML/URide_RoadRoutes_Map.html", "r") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=800, scrolling=True)
    except FileNotFoundError:
        st.error("Error: URide_RoadRoutes_Map.html not found. Please ensure it is in the ML directory.")

if __name__ == "__main__":
    app() 