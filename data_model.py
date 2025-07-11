import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import mysql.connector
from dotenv import load_dotenv
import os

# Charge les variables d'environnement depuis .env (si présent)
load_dotenv()

# Connexion à MySQL avec l'IP de l'hôte, port 3307, sans mot de passe
db = mysql.connector.connect(
    host="192.168.1.80",  # Nouvelle IP de l'hôte
    port=3307,            # Port 3307
    user="root",
    password="",          # Pas de mot de passe
    database="epsi_wis_db"
)
cursor = db.cursor()

# Récupérer les données
def fetch_data():
    cursor.execute("SELECT experience_professionnelle, diplome_niveau_etudes FROM forms_asrbd")
    return pd.DataFrame(cursor.fetchall(), columns=['experience_professionnelle', 'diplome_niveau_etudes'])

# Prétraitement (Bloc 1)
def preprocess_data(df):
    df['experience_pro'] = df['experience_professionnelle'].str.extract('(\d+)').astype(float).fillna(0)
    df = pd.get_dummies(df, columns=['diplome_niveau_etudes'])
    scaler = StandardScaler()
    return scaler.fit_transform(df.dropna())

# Modèle
data = fetch_data()
if not data.empty:
    processed_data = preprocess_data(data)
    kmeans = KMeans(n_clusters=2, random_state=42)
    clusters = kmeans.fit_predict(processed_data)
    print("Clusters des étudiants:", clusters)
else:
    print("Aucune donnée disponible pour le clustering.")