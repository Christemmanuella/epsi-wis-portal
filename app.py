from flask import Flask, request, jsonify
import mysql.connector
from werkzeug.utils import secure_filename
import os
from datamodel import DataModel

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/profile_images'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='root',
    password='',
    database='epsi_wis_db'
)

model = DataModel()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    formation = data.get('formation')
    if not email or not formation:
        return jsonify({'error': 'Email et formation requis'}), 400
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (email_epsi_wis, formation) VALUES (%s, %s)", (email, formation))
    db.commit()
    cursor.close()
    return jsonify({'email': email, 'formation': formation, 'next': 'form'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    cursor = db.cursor()
    cursor.execute("SELECT formation FROM users WHERE email_epsi_wis = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return jsonify({'formation': result[0], 'next': 'dashboard'})
    return jsonify({'error': 'Identifiants invalides'}), 401

@app.route('/validate_session', methods=['GET'])
def validate_session():
    email = request.args.get('email')
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE email_epsi_wis = %s", (email,))
    valid = cursor.fetchone()[0] > 0
    cursor.close()
    return jsonify({'valid': valid})

@app.route('/user_data', methods=['GET'])
def user_data():
    email = request.args.get('email')
    cursor = db.cursor()
    cursor.execute("SELECT formation, form_data FROM users WHERE email_epsi_wis = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        formation, form_data = result
        return jsonify({'formation': formation, 'form': form_data})
    return jsonify({'error': 'Utilisateur non trouvé'}), 404

@app.route('/submit_form', methods=['POST'])
def submit_form():
    data = request.json
    email = data.get('email')
    formation = data.get('formation')
    form_data = {k: v for k, v in data.items() if k not in ['email', 'formation']}
    cursor = db.cursor()
    cursor.execute("UPDATE users SET form_data = %s WHERE email_epsi_wis = %s", (form_data, email))
    db.commit()
    cursor.close()
    return jsonify({'cluster': 0, 'student_count': 1, 'inertia': 0.0})

@app.route('/student_count', methods=['GET'])
def student_count():
    email = request.args.get('email')
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE formation = (SELECT formation FROM users WHERE email_epsi_wis = %s)", (email,))
    count = cursor.fetchone()[0]
    cursor.close()
    return jsonify({'count': count})

@app.route('/change_formation', methods=['POST'])
def change_formation():
    data = request.json
    email = data.get('email')
    cursor = db.cursor()
    cursor.execute("UPDATE users SET formation = NULL WHERE email_epsi_wis = %s", (email,))
    db.commit()
    cursor.close()
    return jsonify({'next': 'form'})

@app.route('/delete_data', methods=['DELETE'])
def delete_data():
    email = request.args.get('email')
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE email_epsi_wis = %s", (email,))
    db.commit()
    cursor.close()
    return jsonify({'message': 'Données supprimées'})

@app.route('/upload_profile_image', methods=['POST'])
def upload_profile_image():
    try:
        if 'profile_image' not in request.files:
            return jsonify({'error': 'Aucun fichier image n\'a été uploadé'}), 400
        file = request.files['profile_image']
        email = request.form.get('email')
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        if file and email:
            filename = secure_filename(f"{email}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            cursor = db.cursor()
            cursor.execute("UPDATE users SET profile_image = %s WHERE email_epsi_wis = %s", (filename, email))
            db.commit()
            cursor.close()

            return jsonify({'success': True, 'message': 'Image uploadée avec succès'})
        return jsonify({'error': 'Données manquantes'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_data', methods=['POST'])
def analyze_data():
    formation = request.json.get('formation')
    data = model.fetch_data(formation)
    clusters, inertia, silhouette = model.train_model(data, formation)
    stats = model.get_descriptive_stats(data, formation)
    if clusters is not None:
        return jsonify({
            'clusters': clusters.tolist(),
            'inertia': inertia,
            'silhouette': silhouette,
            'stats': stats
        })
    return jsonify({'error': 'Données insuffisantes pour l\'analyse'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)