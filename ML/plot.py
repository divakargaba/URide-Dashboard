import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic
import openrouteservice
from openrouteservice import convert

# === Load Data ===
commute_df = pd.read_excel("commute.xlsx")
neighborhood_df = pd.read_excel("Future.xlsx")

# === Clean Columns ===
neighborhood_df.columns = neighborhood_df.columns.str.strip()
neighborhood_df = neighborhood_df.rename(columns={
    "Where do you commute from? Your general neighborhood or quadrant is perfect (e.g., Bowness, NE Calgary, Varsity, Brentwood, etc.)": "Neighborhood"
})
commute_df = commute_df.rename(columns={
    "How do you typically get to campus?": "CommuteMode"
})

# === Merge Datasets ===
min_len = min(len(commute_df), len(neighborhood_df))
merged = pd.concat([
    commute_df[["CommuteMode"]].iloc[:min_len],
    neighborhood_df[["Neighborhood"]].iloc[:min_len]
], axis=1).dropna()

merged["CommuteMode"] = merged["CommuteMode"].str.lower()

# === Classify Users ===
drivers = merged[merged["CommuteMode"].str.contains("drive|car|driving|own vehicle")].copy()
transit_users = merged[merged["CommuteMode"].str.contains("transit|bus|train|c-train")].copy()

print(f"✅ Drivers found: {len(drivers)}")
print(f"✅ Transit users found: {len(transit_users)}")

# === Geocoding Setup ===
geolocator = Nominatim(user_agent="uride_mapper", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=3)

def geocode_location(place):
    try:
        location = geocode(f"{place}, Calgary, Alberta")
        if location:
            return (location.latitude, location.longitude)
    except:
        pass
    return None

# === Geocode Locations ===
drivers["Coordinates"] = drivers["Neighborhood"].apply(geocode_location)
transit_users["Coordinates"] = transit_users["Neighborhood"].apply(geocode_location)

drivers = drivers.dropna(subset=["Coordinates"])
transit_users = transit_users.dropna(subset=["Coordinates"])

drivers[["Lat", "Lon"]] = pd.DataFrame(drivers["Coordinates"].tolist(), index=drivers.index)
transit_users[["Lat", "Lon"]] = pd.DataFrame(transit_users["Coordinates"].tolist(), index=transit_users.index)

# === Set Destination ===
ucalgary_coords = (51.0782, -114.1336)

# === OpenRouteService Client ===
ors_client = openrouteservice.Client(key="5b3ce3597851110001cf6248496eb0f6b094422e9c17eeadd5a538a7")  # Replace this with your actual key

def get_route(coords):
    try:
        route = ors_client.directions(coords, profile='driving-car', format='geojson')
        return route['features'][0]['geometry']['coordinates']
    except Exception as e:
        print(f"Route error for {coords}: {e}")
        return None

# === Create Map ===
m = folium.Map(location=ucalgary_coords, zoom_start=11)
cluster = MarkerCluster().add_to(m)

# === Plot Drivers and Routes ===
for _, row in drivers.iterrows():
    origin = (row["Lat"], row["Lon"])

    # Add driver marker
    folium.Marker(
        location=origin,
        icon=folium.Icon(color="blue"),
        popup=f"DRIVER<br>{row['Neighborhood']}<br>Mode: {row['CommuteMode']}"
    ).add_to(cluster)

    # Add real route to UCalgary
    coords = [(row["Lon"], row["Lat"]), (ucalgary_coords[1], ucalgary_coords[0])]
    route_coords = get_route(coords)

    if route_coords:
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in route_coords],
            color="purple",
            weight=3,
            opacity=0.7
        ).add_to(m)

# === Plot Transit Users ===
for _, rider in transit_users.iterrows():
    rider_coords = (rider["Lat"], rider["Lon"])
    is_match = any(
        geodesic(rider_coords, (driver["Lat"], driver["Lon"])).km <= 2.5
        for _, driver in drivers.iterrows()
    )

    color = "green" if is_match else "red"
    role = "Transit User (Matched)" if is_match else "Transit User"

    folium.Marker(
        location=rider_coords,
        icon=folium.Icon(color=color),
        popup=f"{role}<br>{rider['Neighborhood']}<br>Mode: {rider['CommuteMode']}"
    ).add_to(cluster)

# === Save the Map ===
m.save("URide_RoadRoutes_Map.html")
print("✅ Map saved as URide_RoadRoutes_Map.html")

