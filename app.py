from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
import pandas as pd
from data_model import DataModel

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app)

try:
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'epsi_wis_db')
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Erreur de connexion MySQL : {err}")
    exit(1)

# Créer tables avec toutes les colonnes nécessaires
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email_epsi_wis VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        formation VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forms_asrbd (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE,
        Civilité VARCHAR(10),
        Nom VARCHAR(100),
        Prénom VARCHAR(100),
        Date_de_Naissance DATE,
        Lieu_de_Naissance VARCHAR(100),
        Département_de_Naissance VARCHAR(100),
        Pays VARCHAR(100),
        Adresse VARCHAR(255),
        CP VARCHAR(10),
        Ville VARCHAR(100),
        Tel_Fixe VARCHAR(20),
        Tel_Mobile VARCHAR(20),
        Adresse_mail_personnelle VARCHAR(255),
        Diplôme_ou_niveau_d_études VARCHAR(100),
        Expérience_professionnelle VARCHAR(100),
        Durée_de_l_expérience VARCHAR(20),
        Financement VARCHAR(100),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forms_eisi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE,
        ID_Candidat_IGOR VARCHAR(50),
        Identifiant_candidat VARCHAR(50),
        Campus VARCHAR(100),
        Civilité VARCHAR(10),
        Nom_de_naissance VARCHAR(100),
        Prénom VARCHAR(100),
        Date_de_naissance DATE,
        Code_postal_ville_naissance VARCHAR(10),
        Lieu_de_naissance_ville VARCHAR(100),
        Pays_de_naissance VARCHAR(100),
        Nationalité VARCHAR(100),
        Dernier_diplôme VARCHAR(100),
        Niveau_dernier_diplôme VARCHAR(50),
        Année_d_obtention INT,
        Décision_du_jury VARCHAR(50),
        Année_de_première_inscription INT,
        Voie_d_accès VARCHAR(100),
        Situation_avant_cursus VARCHAR(100),
        Dernier_métier VARCHAR(100),
        Nom_de_l_entreprise VARCHAR(100),
        Durée_de_l_expérience VARCHAR(20),
        Téléphone_portable VARCHAR(20),
        Adresse_mail_personnelle VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forms_devia (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE,
        ID_Candidat_IGOR VARCHAR(50),
        Identifiant_candidat VARCHAR(50),
        Campus VARCHAR(100),
        Civilité VARCHAR(10),
        Nom_de_naissance VARCHAR(100),
        Prénom VARCHAR(100),
        Date_de_naissance DATE,
        Code_postal_ville_naissance VARCHAR(10),
        Lieu_de_naissance_ville VARCHAR(100),
        Pays_de_naissance VARCHAR(100),
        Nationalité VARCHAR(100),
        Dernier_diplôme VARCHAR(100),
        Niveau_dernier_diplôme VARCHAR(50),
        Année_d_obtention INT,
        Décision_du_jury VARCHAR(50),
        Année_de_première_inscription INT,
        Voie_d_accès VARCHAR(100),
        Situation_avant_cursus VARCHAR(100),
        Dernier_métier VARCHAR(100),
        Nom_de_l_entreprise VARCHAR(100),
        Durée_de_l_expérience VARCHAR(20),
        Téléphone_portable VARCHAR(20),
        Adresse_mail_personnelle VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
db.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    print(f"Données reçues: {data}")
    if not data or 'email' not in data or 'formation' not in data:
        return jsonify({'error': 'Données manquantes (email ou formation)'}), 400
    email = data['email']
    formation = data['formation']
    if not (email.endswith('@ecoles-epsi.net') or email.endswith('@ecoles-wis.net')):
        return jsonify({'error': 'Email invalide'}), 400
    try:
        cursor.execute("SELECT id FROM users WHERE email_epsi_wis = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email déjà utilisé'}), 400
        cursor.execute("INSERT INTO users (email_epsi_wis, formation) VALUES (%s, %s)", (email, formation))
        db.commit()
        print(f"Utilisateur inscrit : {email}")
        return jsonify({'message': 'Inscription réussie', 'next': 'form', 'email': email, 'formation': formation})
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Erreur MySQL : {err}")
        return jsonify({'error': f'Erreur de base de données : {str(err)}'}), 500
    except Exception as err:
        db.rollback()
        print(f"Erreur inattendue : {err}")
        return jsonify({'error': f'Erreur inattendue : {str(err)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    cursor.execute("SELECT * FROM users WHERE email_epsi_wis = %s", (data['email'],))
    user = cursor.fetchone()
    if user and (not user[2] or user[2] == data.get('password', '')):
        session['user_id'] = user[0]
        return jsonify({'message': 'Connexion réussie', 'next': 'dashboard', 'formation': user[3]})
    return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        data = request.json
        print("Données reçues:", data)  # Log des données reçues
        if not data or 'email' not in data:
            return jsonify({'error': 'Données manquantes (email requis)'}), 400
        email = data.get('email')
        password = data.get('Password', '')
        cursor.execute("SELECT id FROM users WHERE email_epsi_wis = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        user_id = user[0]
        if password:
            cursor.execute("UPDATE users SET password = %s WHERE email_epsi_wis = %s", (password, email))

        formation = data.get('formation', '')
        print(f"Formation détectée : {formation}")  # Débogage
        if formation == 'ASRBD':
            date_naissance = data.get('Date_de_Naissance', None) if data.get('Date_de_Naissance') else None
            cursor.execute("""
                INSERT INTO forms_asrbd (user_id, Civilité, Nom, Prénom, Date_de_Naissance, Lieu_de_Naissance,
                Département_de_Naissance, Pays, Adresse, CP, Ville, Tel_Fixe, Tel_Mobile,
                Adresse_mail_personnelle, Diplôme_ou_niveau_d_études, Expérience_professionnelle,
                Durée_de_l_expérience, Financement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                Civilité=VALUES(Civilité), Nom=VALUES(Nom), Prénom=VALUES(Prénom), Date_de_Naissance=VALUES(Date_de_Naissance),
                Lieu_de_Naissance=VALUES(Lieu_de_Naissance), Département_de_Naissance=VALUES(Département_de_Naissance),
                Pays=VALUES(Pays), Adresse=VALUES(Adresse), CP=VALUES(CP), Ville=VALUES(Ville), Tel_Fixe=VALUES(Tel_Fixe),
                Tel_Mobile=VALUES(Tel_Mobile), Adresse_mail_personnelle=VALUES(Adresse_mail_personnelle),
                Diplôme_ou_niveau_d_études=VALUES(Diplôme_ou_niveau_d_études), Expérience_professionnelle=VALUES(Expérience_professionnelle),
                Durée_de_l_expérience=VALUES(Durée_de_l_expérience), Financement=VALUES(Financement)""",
                (user_id, data.get('Civilité', ''), data.get('Nom', ''), data.get('Prénom', ''),
                 date_naissance, data.get('Lieu_de_Naissance', ''), data.get('Département_de_Naissance', ''),
                 data.get('Pays', ''), data.get('Adresse', ''), data.get('CP', ''), data.get('Ville', ''),
                 data.get('Tel_Fixe', ''), data.get('Tel_Mobile', ''), data.get('Adresse_mail_personnelle', ''),
                 data.get('Diplôme_ou_niveau_d_études', ''), data.get('Expérience_professionnelle', ''),
                 data.get('Durée_de_l_expérience', ''), data.get('Financement', '')))
        elif formation in ['EISI', 'DEVIA']:
            date_naissance = data.get('Date_de_naissance', None) if data.get('Date_de_naissance') else None
            table = 'forms_eisi' if formation == 'EISI' else 'forms_devia'
            cursor.execute(f"""
                INSERT INTO {table} (user_id, ID_Candidat_IGOR, Identifiant_candidat, Campus, Civilité, Nom_de_naissance,
                Prénom, Date_de_naissance, Code_postal_ville_naissance, Lieu_de_naissance_ville, Pays_de_naissance,
                Nationalité, Dernier_diplôme, Niveau_dernier_diplôme, Année_d_obtention, Décision_du_jury,
                Année_de_première_inscription, Voie_d_accès, Situation_avant_cursus, Dernier_métier, Nom_de_l_entreprise,
                Durée_de_l_expérience, Téléphone_portable, Adresse_mail_personnelle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                ID_Candidat_IGOR=VALUES(ID_Candidat_IGOR), Identifiant_candidat=VALUES(Identifiant_candidat), Campus=VALUES(Campus),
                Civilité=VALUES(Civilité), Nom_de_naissance=VALUES(Nom_de_naissance), Prénom=VALUES(Prénom),
                Date_de_naissance=VALUES(Date_de_naissance), Code_postal_ville_naissance=VALUES(Code_postal_ville_naissance),
                Lieu_de_naissance_ville=VALUES(Lieu_de_naissance_ville), Pays_de_naissance=VALUES(Pays_de_naissance),
                Nationalité=VALUES(Nationalité), Dernier_diplôme=VALUES(Dernier_diplôme), Niveau_dernier_diplôme=VALUES(Niveau_dernier_diplôme),
                Année_d_obtention=VALUES(Année_d_obtention), Décision_du_jury=VALUES(Décision_du_jury),
                Année_de_première_inscription=VALUES(Année_de_première_inscription), Voie_d_accès=VALUES(Voie_d_accès),
                Situation_avant_cursus=VALUES(Situation_avant_cursus), Dernier_métier=VALUES(Dernier_métier),
                Nom_de_l_entreprise=VALUES(Nom_de_l_entreprise), Durée_de_l_expérience=VALUES(Durée_de_l_expérience),
                Téléphone_portable=VALUES(Téléphone_portable), Adresse_mail_personnelle=VALUES(Adresse_mail_personnelle)""",
                (user_id, data.get('ID_Candidat_IGOR', ''), data.get('Identifiant_candidat', ''), data.get('Campus', ''),
                 data.get('Civilité', ''), data.get('Nom_de_naissance', ''), data.get('Prénom', ''),
                 date_naissance, data.get('Code_postal_ville_naissance', ''), data.get('Lieu_de_naissance_ville', ''),
                 data.get('Pays_de_naissance', ''), data.get('Nationalité', ''), data.get('Dernier_diplôme', ''),
                 data.get('Niveau_dernier_diplôme', ''), data.get('Année_d_obtention', None),
                 data.get('Décision_du_jury', ''), data.get('Année_de_première_inscription', None),
                 data.get('Voie_d_accès', ''), data.get('Situation_avant_cursus', ''), data.get('Dernier_métier', ''),
                 data.get('Nom_de_l_entreprise', ''), data.get('Durée_de_l_expérience', ''),
                 data.get('Téléphone_portable', ''), data.get('Adresse_mail_personnelle', '')))
        db.commit()
        print(f"Données insérées ou mises à jour pour user_id: {user_id}")

        model = DataModel()
        if formation == 'ASRBD':
            cursor.execute("SELECT Durée_de_l_expérience, Diplôme_ou_niveau_d_études FROM forms_asrbd WHERE user_id = %s", (user_id,))
        elif formation in ['EISI', 'DEVIA']:
            cursor.execute("SELECT Durée_de_l_expérience, Niveau_dernier_diplôme FROM forms_eisi WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        student_count = 1  # Par défaut, l'utilisateur courant
        cursor.execute("SELECT COUNT(*) FROM users WHERE formation = %s", (formation,))
        total_students = cursor.fetchone()[0]
        if total_students > 1:
            student_count = total_students

        if rows:
            df = pd.DataFrame(rows, columns=['Durée_de_l_expérience', 'Diplôme_ou_niveau_d_études' if formation == 'ASRBD' else 'Niveau_dernier_diplôme'])
            clusters, inertia = model.train_model(df, formation)
            if clusters is not None and len(clusters) > 0:
                print(f"Clusters générés : {clusters}")
                print(f"Inertie : {inertia}")
                user_cluster = clusters[-1] if len(clusters) == len(rows) else None
                return jsonify({'message': 'Formulaire soumis', 'next': 'login', 'cluster': user_cluster, 'student_count': student_count, 'inertia': inertia}), 200
        print("Pas assez de données pour le clustering ou aucune donnée récupérée.")
        return jsonify({'message': 'Formulaire soumis (clustering en attente)', 'next': 'login', 'cluster': None, 'student_count': student_count, 'inertia': None}), 200
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Erreur MySQL : {str(err)}")
        return jsonify({'error': f'Erreur de base de données : {str(err)}'}), 500
    except KeyError as err:
        db.rollback()
        print(f"Clé manquante dans les données : {str(err)}")
        return jsonify({'error': f'Clé manquante : {str(err)}'}), 400
    except Exception as err:
        db.rollback()
        print(f"Erreur inattendue : {str(err)}")
        return jsonify({'error': f'Erreur inattendue : {str(err)}'}), 500

@app.route('/user_data')
def user_data():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email requis'}), 400
    cursor.execute("SELECT id, formation FROM users WHERE email_epsi_wis = %s", (email,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'form': {}, 'formation': None})
    user_id, formation = user
    form_data = {}
    if formation == 'ASRBD':
        cursor.execute("SELECT * FROM forms_asrbd WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            form_data = dict(zip([desc[0] for desc in cursor.description], result))
            print(f"Données récupérées pour user_id {user_id}: {form_data}")
    elif formation == 'EISI':
        cursor.execute("SELECT * FROM forms_eisi WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            form_data = dict(zip([desc[0] for desc in cursor.description], result))
            print(f"Données récupérées pour user_id {user_id}: {form_data}")
    elif formation == 'DEVIA':
        cursor.execute("SELECT * FROM forms_devia WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            form_data = dict(zip([desc[0] for desc in cursor.description], result))
            print(f"Données récupérées pour user_id {user_id}: {form_data}")
    return jsonify({'form': form_data, 'formation': formation})

@app.route('/validate_session', methods=['GET'])
def validate_session():
    email = request.args.get('email')
    if not email:
        return jsonify({'valid': False})
    cursor.execute("SELECT id FROM users WHERE email_epsi_wis = %s", (email,))
    user = cursor.fetchone()
    if user and session.get('user_id'):
        return jsonify({'valid': True})
    return jsonify({'valid': False})

@app.route('/delete_data', methods=['DELETE'])
def delete_data():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email requis'}), 400
    cursor.execute("SELECT id FROM users WHERE email_epsi_wis = %s", (email,))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        cursor.execute("DELETE FROM forms_asrbd WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM forms_eisi WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM forms_devia WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        session.pop('user_id', None)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/change_formation', methods=['POST'])
def change_formation():
    data = request.json
    email = data['email']
    formation = data['formation']
    cursor.execute("UPDATE users SET formation = %s WHERE email_epsi_wis = %s", (formation, email))
    cursor.execute("DELETE FROM forms_asrbd WHERE user_id IN (SELECT id FROM users WHERE email_epsi_wis = %s)", (email,))
    cursor.execute("DELETE FROM forms_eisi WHERE user_id IN (SELECT id FROM users WHERE email_epsi_wis = %s)", (email,))
    cursor.execute("DELETE FROM forms_devia WHERE user_id IN (SELECT id FROM users WHERE email_epsi_wis = %s)", (email,))
    db.commit()
    return jsonify({'message': 'Formation changée', 'next': 'form', 'email': email, 'formation': formation})

@app.route('/student_count', methods=['GET'])
def student_count():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email requis'}), 400
    cursor.execute("SELECT formation FROM users WHERE email_epsi_wis = %s", (email,))
    user = cursor.fetchone()
    if user:
        formation = user[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE formation = %s", (formation,))
        count = cursor.fetchone()[0]
        return jsonify({'count': count, 'formation': formation})
    return jsonify({'count': 0})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        cursor.close()
        db.close()