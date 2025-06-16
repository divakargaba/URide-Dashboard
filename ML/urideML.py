# URide ML Analysis Script

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report

# Load the data (adjust path as needed)
df1 = pd.read_excel("commute.xlsx")
df2 = pd.read_excel("Future.xlsx")

# ----------------------------
# SECTION 1: COMMUTE ANALYSIS
# ----------------------------

df1.columns = df1.columns.str.strip().str.replace('\n', ' ').str.replace('\r', ' ').str.replace(' +', ' ', regex=True)

# Clean commute time

def extract_minutes(val):
    try:
        return float(val)
    except:
        if 'mins' in str(val).lower():
            num = ''.join(filter(str.isdigit, str(val)))
            return float(num) if num else np.nan
        return np.nan

df1["Commute Time (mins)"] = df1["How much time does your commute take on average? (One-Way)"].apply(extract_minutes)

# Frustration Score Description
print("\n--- Commute Frustration Stats ---")
print(df1['On a scale from 1 to 10, how frustrating is your daily commute?'].describe())

# Commute Mode Distribution
print("\n--- Commute Mode Distribution ---")
print(df1['How do you typically get to campus?'].value_counts())

# ----------------------------
# SECTION 2: VISUALIZATIONS
# ----------------------------

df2.columns = df2.columns.str.strip().str.replace('\n', ' ').str.replace('\r', ' ').str.replace(' +', ' ', regex=True)

# Preferred Pricing
rider_price_series = df2["Riders: How much would you consider a reasonable/fair price for a one-way ride to campus?"].dropna()
cleaned_prices = rider_price_series.str.strip().value_counts()

plt.figure()
cleaned_prices.plot(kind='bar')
plt.title("Preferred One-Way Ride Price")
plt.ylabel("Count")
plt.xlabel("Price Range")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output_plot.png")


# Word Cloud: First Impressions
text = " ".join(df2["What’s your first impression of URide? (Open-ended)"].dropna().astype(str).tolist())
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.title("First Impressions of URide")
plt.savefig("output_plot.png")


# ----------------------------
# SECTION 3: CLUSTERING
# ----------------------------
cluster_data = df1[[
    "How do you typically get to campus?",
    "Commute Time (mins)",
    "Do you think your commute costs too much?",
    "Have you ever felt unsafe commuting to/from Campus? (on Transit, Uber, walking, etc..)?",
    "Does your commute feel lonely, boring, or disconnected?",
    "On a scale from 1 to 10, how frustrating is your daily commute?"
]].dropna()

cluster_data = cluster_data.rename(columns={
    "How do you typically get to campus?": "Commute Mode",
    "Do you think your commute costs too much?": "Cost Concern",
    "Have you ever felt unsafe commuting to/from Campus? (on Transit, Uber, walking, etc..)?": "Felt Unsafe",
    "Does your commute feel lonely, boring, or disconnected?": "Disconnected",
    "On a scale from 1 to 10, how frustrating is your daily commute?": "Frustration"
})

le = LabelEncoder()
for col in ["Commute Mode", "Cost Concern", "Felt Unsafe", "Disconnected"]:
    cluster_data[col] = le.fit_transform(cluster_data[col].astype(str))

X_cluster = cluster_data.dropna().values
kmeans = KMeans(n_clusters=4, random_state=42)
cluster_data["Cluster"] = kmeans.fit_predict(X_cluster)
print("\n--- Cluster Summary ---")
print(cluster_data.groupby("Cluster").mean().round(2))

# ----------------------------
# SECTION 4: LOGISTIC REGRESSION PREDICTION
# ----------------------------
usage_raw = df2["Would you use URide?"].dropna()
mapped_usage = usage_raw.apply(lambda x: 1 if str(x).strip().lower() == "yes" else 0)

df_filtered = df2.loc[mapped_usage.index]

feature_cols = [
    "How much Do You Spend Weekly/Monthly on Commuting? (If unsure, just list the stuff you know you typically pay for, UPass, parking pass, etc.)",
    "What pricing structure would you prefer for URide?",
    "How do you feel about riding with new people from your campus?",
    "How important is a preference feature for comfortability? (e.g. Quiet/More Social Rides, women-only rides, etc.)?",
    "Would you pay for premium features (e.g., exclusive features, free rides/discounts, event deals)?"
]

ml_df = df_filtered[feature_cols].copy()
ml_df["target"] = mapped_usage
ml_df = ml_df.dropna()

for col in feature_cols:
    ml_df[col] = LabelEncoder().fit_transform(ml_df[col].astype(str))

X = ml_df.drop(columns=["target"])
y = ml_df["target"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression()
model.fit(X_train_scaled, y_train)
y_pred = model.predict(X_test_scaled)

print("\n--- URide Usage Prediction Report ---")
print(classification_report(y_test, y_pred))
