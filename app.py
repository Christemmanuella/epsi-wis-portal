from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
import re  # Pour les expressions régulières

# Charge les variables d'environnement depuis .env (si présent)
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app)

# Connexion à MySQL
db = mysql.connector.connect(
    host="192.168.1.80",
    port=3307,
    user="root",
    password="",
    database="epsi_wis_db"
)
cursor = db.cursor()

# Créer tables
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
        user_id INT,
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
        Expérience_professionnelle VARCHAR(255),
        Financement VARCHAR(100),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forms_eisi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
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
        Durée_de_l_expérience INT,
        Téléphone_portable VARCHAR(20),
        Adresse_mail_personnelle VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS forms_devia (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
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
        Durée_de_l_expérience INT,
        Téléphone_portable VARCHAR(20),
        Adresse_mail_personnelle VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")
db.commit()

# Route principale
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data['email']
    formation = data['formation']
    if not (email.endswith('@ecoles-epsi.net') or email.endswith('@ecoles-wis.net')):
        return jsonify({'error': 'Email invalide'}), 400
    cursor.execute("SELECT id FROM users WHERE email_epsi_wis = %s", (email,))
    if cursor.fetchone():
        return jsonify({'error': 'Email déjà utilisé'}), 400
    cursor.execute("INSERT INTO users (email_epsi_wis, formation) VALUES (%s, %s)", (email, formation))
    db.commit()
    print(f"Utilisateur inscrit : {email}")  # Débogage
    return jsonify({'message': 'Inscription réussie', 'next': 'form', 'email': email, 'formation': formation})

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
        print("Données reçues:", data)  # Débogage
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
        if formation == 'ASRBD':
            date_naissance = data.get('Date_de_Naissance')  # Pas de validation stricte pour l'instant
            cursor.execute("""
                INSERT INTO forms_asrbd (user_id, Civilité, Nom, Prénom, Date_de_Naissance, Lieu_de_Naissance, 
                Département_de_Naissance, Pays, Adresse, CP, Ville, Tel_Fixe, Tel_Mobile, Adresse_mail_personnelle, 
                Diplôme_ou_niveau_d_études, Expérience_professionnelle, Financement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, data.get('Civilité', ''), data.get('Nom', ''), data.get('Prénom', ''), 
                 date_naissance or None, data.get('Lieu_de_Naissance', ''), 
                 data.get('Département_de_Naissance', ''), data.get('Pays', ''), data.get('Adresse', ''), 
                 data.get('CP', ''), data.get('Ville', ''), data.get('Tel_Fixe', ''), data.get('Tel_Mobile', ''), 
                 data.get('Adresse_mail_personnelle', ''), data.get('Diplôme_ou_niveau_d_études', ''), 
                 data.get('Expérience_professionnelle', ''), data.get('Financement', '')))
        elif formation == 'EISI':
            date_naissance = data.get('Date_de_naissance')
            cursor.execute("""
                INSERT INTO forms_eisi (user_id, ID_Candidat_IGOR, Identifiant_candidat, Campus, Civilité, Nom_de_naissance, 
                Prénom, Date_de_naissance, Code_postal_ville_naissance, Lieu_de_naissance_ville, Pays_de_naissance, 
                Nationalité, Dernier_diplôme, Niveau_dernier_diplôme, Année_d_obtention, Décision_du_jury, 
                Année_de_première_inscription, Voie_d_accès, Situation_avant_cursus, Dernier_métier, Nom_de_l_entreprise, 
                Durée_de_l_expérience, Téléphone_portable, Adresse_mail_personnelle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, data.get('ID_Candidat_IGOR', ''), data.get('Identifiant_candidat', ''), data.get('Campus', ''), 
                 data.get('Civilité', ''), data.get('Nom_de_naissance', ''), data.get('Prénom', ''), 
                 date_naissance or None, data.get('Code_postal_ville_naissance', ''), 
                 data.get('Lieu_de_naissance_ville', ''), data.get('Pays_de_naissance', ''), data.get('Nationalité', ''), 
                 data.get('Dernier_diplôme', ''), data.get('Niveau_dernier_diplôme', ''), 
                 data.get('Année_d_obtention', None), data.get('Décision_du_jury', ''), 
                 data.get('Année_de_première_inscription', None), data.get('Voie_d_accès', ''), 
                 data.get('Situation_avant_cursus', ''), data.get('Dernier_métier', ''), 
                 data.get('Nom_de_l_entreprise', ''), data.get('Durée_de_l_expérience', None), 
                 data.get('Téléphone_portable', ''), data.get('Adresse_mail_personnelle', '')))
        elif formation == 'DEVIA':
            date_naissance = data.get('Date_de_naissance')
            cursor.execute("""
                INSERT INTO forms_devia (user_id, ID_Candidat_IGOR, Identifiant_candidat, Campus, Civilité, Nom_de_naissance, 
                Prénom, Date_de_naissance, Code_postal_ville_naissance, Lieu_de_naissance_ville, Pays_de_naissance, 
                Nationalité, Dernier_diplôme, Niveau_dernier_diplôme, Année_d_obtention, Décision_du_jury, 
                Année_de_première_inscription, Voie_d_accès, Situation_avant_cursus, Dernier_métier, Nom_de_l_entreprise, 
                Durée_de_l_expérience, Téléphone_portable, Adresse_mail_personnelle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, data.get('ID_Candidat_IGOR', ''), data.get('Identifiant_candidat', ''), data.get('Campus', ''), 
                 data.get('Civilité', ''), data.get('Nom_de_naissance', ''), data.get('Prénom', ''), 
                 date_naissance or None, data.get('Code_postal_ville_naissance', ''), 
                 data.get('Lieu_de_naissance_ville', ''), data.get('Pays_de_naissance', ''), data.get('Nationalité', ''), 
                 data.get('Dernier_diplôme', ''), data.get('Niveau_dernier_diplôme', ''), 
                 data.get('Année_d_obtention', None), data.get('Décision_du_jury', ''), 
                 data.get('Année_de_première_inscription', None), data.get('Voie_d_accès', ''), 
                 data.get('Situation_avant_cursus', ''), data.get('Dernier_métier', ''), 
                 data.get('Nom_de_l_entreprise', ''), data.get('Durée_de_l_expérience', None), 
                 data.get('Téléphone_portable', ''), data.get('Adresse_mail_personnelle', '')))
        db.commit()
        print(f"Données insérées pour user_id: {user_id}")  # Débogage supplémentaire
        return jsonify({'message': 'Formulaire soumis', 'next': 'login'}), 200
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Erreur MySQL : {str(err)}")  # Débogage
        return jsonify({'error': f'Erreur de base de données : {str(err)}'}), 500
    except KeyError as err:
        return jsonify({'error': f'Clé manquante dans les données : {str(err)}'}), 400
    except Exception as err:
        db.rollback()
        print(f"Erreur inattendue : {str(err)}")  # Débogage
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
            print(f"Données récupérées pour user_id {user_id}: {form_data}")  # Débogage
    elif formation == 'EISI':
        cursor.execute("SELECT * FROM forms_eisi WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            form_data = dict(zip([desc[0] for desc in cursor.description], result))
            print(f"Données récupérées pour user_id {user_id}: {form_data}")  # Débogage
    elif formation == 'DEVIA':
        cursor.execute("SELECT * FROM forms_devia WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            form_data = dict(zip([desc[0] for desc in cursor.description], result))
            print(f"Données récupérées pour user_id {user_id}: {form_data}")  # Débogage
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)