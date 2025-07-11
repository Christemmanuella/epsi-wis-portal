EPSI-WIS Student Portal
Description
Plateforme pour les étudiants EPSI et WIS permettant l'inscription, la soumission de formulaires spécifiques (ASRBD, EISI, DEVIA), et la gestion des données avec un modèle pour l'IA.
Installation

Installez Python, Docker, et MySQL Workbench.
Configurez une base de données epsi_wis_db avec les tables SQL.
Installez les dépendances : pip install -r requirements.txt.
Placez les logos dans assets/.
Lancez avec Docker : docker build -t epsi_wis_portal . puis docker run -p 5000:5000 epsi_wis_portal.

Utilisation

Accédez à http://localhost:5000 pour tester (à connecter plus tard).
Inscrivez-vous avec un email @ecoles-epsi.net ou @ecoles-wis.net.
Connectez-vous et remplissez le formulaire.

Bloc 1 : Modèle de données pour IA
Les données sont stockées dans MySQL et prétraitées avec data_model.py pour un clustering (ex. : profiler les étudiants par expérience et diplôme).
Contributeurs

[Christ Emmanuela Mondah]
