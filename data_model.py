import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import mysql.connector
from dotenv import load_dotenv
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charge les variables d'environnement depuis .env (si présent)
load_dotenv()

class DataModel:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3307)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'epsi_wis_db')
        )
        self.cursor = self.conn.cursor()

    def fetch_data(self, formation):
        """Récupère les données des étudiants depuis la BDD selon la formation."""
        try:
            if formation == 'ASRBD':
                self.cursor.execute("SELECT experience_professionnelle, diplome_ou_niveau_d_etudes FROM forms_asrbd")
                rows = self.cursor.fetchall()
                return pd.DataFrame(rows, columns=['experience_professionnelle', 'diplome_ou_niveau_d_etudes'])
            elif formation in ['EISI', 'DEVIA']:
                self.cursor.execute("SELECT duree_de_l_experience, niveau_dernier_diplome FROM forms_eisi")
                rows = self.cursor.fetchall()
                return pd.DataFrame(rows, columns=['duree_de_l_experience', 'niveau_dernier_diplome'])
            return pd.DataFrame()
        except mysql.connector.Error as e:
            logger.error(f"Erreur MySQL : {e}")
            return pd.DataFrame()

    def preprocess_data(self, df, formation):
        """Prétraite les données pour le clustering selon la formation."""
        if df.empty:
            return None
        if formation == 'ASRBD':
            df['experience_pro'] = df['experience_professionnelle'].map({'Débutant': 0, 'Junior': 2, 'Confirmé': 4, 'Senior': 6}).fillna(0)
            df = pd.get_dummies(df, columns=['diplome_ou_niveau_d_etudes'])
        elif formation in ['EISI', 'DEVIA']:
            df['experience_pro'] = df['duree_de_l_experience'].map({'0-2 ans': 1, '3-5 ans': 4, '6-10 ans': 8, '10+ ans': 12}).fillna(0)
            df = pd.get_dummies(df, columns=['niveau_dernier_diplome'])
        scaler = StandardScaler()
        return scaler.fit_transform(df)

    def train_model(self, df, formation):
        """Entraîne un modèle KMeans et retourne les clusters avec métriques."""
        if df is None or df.empty or len(df) < 2:
            return None, None, None
        processed_data = self.preprocess_data(df, formation)
        if processed_data is None:
            return None, None, None
        kmeans = KMeans(n_clusters=2, random_state=42)
        clusters = kmeans.fit_predict(processed_data)
        inertia = kmeans.inertia_
        silhouette = silhouette_score(processed_data, clusters) if len(processed_data) > 1 else None
        return clusters, inertia, silhouette

    def get_descriptive_stats(self, df, formation):
        """Retourne des statistiques descriptives."""
        if df.empty:
            return None
        if formation == 'ASRBD':
            return df['experience_professionnelle'].value_counts().to_dict()
        elif formation in ['EISI', 'DEVIA']:
            return df['duree_de_l_experience'].value_counts().to_dict()
        return None

    def close(self):
        """Ferme la connexion à la BDD."""
        self.conn.close()

if __name__ == "__main__":
    model = DataModel()
    data = model.fetch_data('DEVIA')
    clusters, inertia, silhouette = model.train_model(data, 'DEVIA')
    stats = model.get_descriptive_stats(data, 'DEVIA')
    if clusters is not None:
        logger.info(f"Clusters des étudiants : {clusters}")
        logger.info(f"Inertie : {inertia}")
        logger.info(f"Score Silhouette : {silhouette}")
    else:
        logger.info("Aucun clustering effectué (données manquantes ou insuffisantes).")
    if stats:
        logger.info(f"Statistiques descriptives : {stats}")
    model.close()