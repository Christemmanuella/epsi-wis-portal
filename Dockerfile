# Utilise une image Python officielle comme image parent
FROM python:3.9-slim

# Définit le répertoire de travail
WORKDIR /app

# Installe netcat
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copie le fichier des dépendances
COPY requirements.txt .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie le script d'attente
COPY wait-for-it.sh .

# Copie le reste de l'application
COPY . .

# Expose le port
EXPOSE 5000

# Lance l'application après avoir attendu la base de données
CMD ["./wait-for-it.sh", "db:3306", "--", "python", "app.py"]