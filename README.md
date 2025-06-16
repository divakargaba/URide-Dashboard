# URide Dashboard

A Streamlit-based dashboard for visualizing URide driver and transit user routes.

## Features

- Interactive map visualization of driver and transit user routes
- Static road route visualization using Folium
- Clean and responsive UI

## Setup

1. Install the required packages:
```bash
pip install streamlit pandas folium geopy openrouteservice openpyxl
```

2. Run the dashboard:
```bash
streamlit run ML/dashboard.py
```

## Project Structure

- `ML/dashboard.py`: Main Streamlit dashboard application
- `ML/URide_RoadRoutes_Map.html`: Static map visualization
- `ML/plot.py`: Original map generation script 