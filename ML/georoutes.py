import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic

# === Load Datasets ===
commute_data = pd.read_excel("commute.xlsx")
neighborhood_data = pd.read_excel("Future.xlsx")

# === Clean and Standardize ===
commute_data = commute_data.rename(columns={
    "How do you typically get to campus?": "CommuteMode"
})

# Strip extra whitespace in column headers
neighborhood_data.columns = neighborhood_data.columns.str.strip()

neighborhood_data = neighborhood_data.rename(columns={
    "Where do you commute from? Your general neighborhood or quadrant is perfect (e.g., Bowness, NE Calgary, Varsity, Brentwood, etc.)": "Neighborhood"
})

# Merge datasets by index
min_len = min(len(commute_data), len(neighborhood_data))
merged_df = pd.concat([
    commute_data[["CommuteMode"]].iloc[:min_len],
    neighborhood_data[["Neighborhood"]].iloc[:min_len]
], axis=1).dropna()

# === Classify ===
drivers = merged_df[merged_df["CommuteMode"].str.lower().str.contains("drive|car")].copy()
transit_users = merged_df[merged_df["CommuteMode"].str.lower().str.contains("transit|bus")].copy()

# === Geocode Setup ===
geolocator = Nominatim(user_agent="uride_mapper", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=3, error_wait_seconds=5)


def geocode_location(place):
    try:
        location = geocode(f"{place}, Calgary, Alberta")
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None


# === Geocode Neighborhoods ===
drivers.loc[:, "Coordinates"] = drivers["Neighborhood"].apply(geocode_location)
transit_users.loc[:, "Coordinates"] = transit_users["Neighborhood"].apply(geocode_location)

# Drop rows where geocoding failed
drivers = drivers.dropna(subset=["Coordinates"])
transit_users = transit_users.dropna(subset=["Coordinates"])

# === Split Coordinates ===
drivers_latlon = pd.DataFrame(drivers["Coordinates"].tolist(), columns=["DriverLat", "DriverLon"])
transit_latlon = pd.DataFrame(transit_users["Coordinates"].tolist(), columns=["RiderLat", "RiderLon"])

drivers = pd.concat([drivers.reset_index(drop=True), drivers_latlon], axis=1)
transit_users = pd.concat([transit_users.reset_index(drop=True), transit_latlon], axis=1)

# === Map Setup ===
ucalgary_coords = (51.0782, -114.1336)
m = folium.Map(location=ucalgary_coords, zoom_start=11)
marker_cluster = MarkerCluster().add_to(m)

# === Plot Drivers, Routes, and Matched Riders ===
for _, driver in drivers.iterrows():
    driver_origin = (driver["DriverLat"], driver["DriverLon"])

    # Driver Marker
    folium.Marker(
        location=driver_origin,
        icon=folium.Icon(color='blue'),
        popup=f"Driver from {driver['Neighborhood']}"
    ).add_to(marker_cluster)

    # Route Line
    folium.PolyLine([driver_origin, ucalgary_coords], color="purple", weight=2.5, opacity=0.7).add_to(m)

    # Check nearby transit users
    for _, rider in transit_users.iterrows():
        rider_origin = (rider["RiderLat"], rider["RiderLon"])
        distance_km = geodesic(driver_origin, rider_origin).km
        if distance_km <= 2.5:
            folium.Marker(
                location=rider_origin,
                icon=folium.Icon(color='green'),
                popup=f"Transit User (Match) from {rider['Neighborhood']}"
            ).add_to(marker_cluster)
        else:
            folium.Marker(
                location=rider_origin,
                icon=folium.Icon(color='red'),
                popup=f"Transit User from {rider['Neighborhood']}"
            ).add_to(marker_cluster)

# === Export Map ===
m.save("URide_Rider_Driver_Match_Map.html")
print("✅ Map saved as URide_Rider_Driver_Match_Map.html")

