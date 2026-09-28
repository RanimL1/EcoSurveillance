# EcoSurveillance

Plateforme intelligente de surveillance environnementale — Détection automatique des infractions de jet de déchets par vision par ordinateur et IA.


---

## Table des matières

- [À propos](#à-propos)
- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
  - [Backend Spring Boot](#1-backend-spring-boot)
  - [Frontend Angular](#2-frontend-angular)
  - [Module IA Python](#3-module-ia-python)
- [Configuration](#configuration)
- [Structure du projet](#structure-du-projet)
- [Auteure](#auteure)

---

## À propos

EcoSurveillance est une plateforme de surveillance intelligente qui détecte automatiquement les infractions de jet de déchets dans les espaces publics en combinant :

- La détection d'objets (YOLOv8) pour identifier personnes et déchets
- Le tracking multi-objets (DeepSORT) pour suivre les individus
- L'analyse comportementale AOI pour détecter les gestes de jet
- La reconnaissance faciale (ArcFace) pour identifier les contrevenants
- Une application web complète pour la gestion des infractions

---

## Architecture

```
ecosurveillance-back/    →  API REST Spring Boot (port 8081)
ecosurveillance-front/   →  Interface Angular 17  (port 4200)
ecosurveillance-ia/      →  Pipeline IA Python
```

Flux de détection :

```
Caméra → YOLOv8 → DeepSORT → AOI Pipeline → Reconnaissance faciale → Backend → Frontend
```

Le module IA communique avec le backend via HTTP multipart sur l'endpoint `/api/detections/python`.

---

## Fonctionnalités

### Module IA
- Détection temps réel de personnes et déchets (YOLOv8m, imgsz=1280)
- Tracking multi-objets avec DeepSORT
- Analyse comportementale par keypoints (distance poignet-déchet)
- Trajectoire et accélération pour distinguer jet vs dépôt
- Reconnaissance faciale ArcFace par distance cosinus
- Gestion des déchets préexistants (anti faux positifs)
- Envoi asynchrone au backend avec retry automatique
- Support GPU (CUDA) et CPU

### Backend
- API REST sécurisée (Spring Security + JWT)
- Gestion des utilisateurs : Administrateur et Étudiant
- Réception des alertes IA (photo + vidéo)
- Gestion des infractions et preuves
- Base de données MySQL

### Frontend
- Dashboard administrateur
- Consultation des infractions en temps réel
- Gestion des étudiants et des preuves
- Interface responsive Angular 17

---

## Prérequis

- Python 3.10 ou supérieur
- Java JDK 17 ou supérieur
- Node.js 18 ou supérieur
- MySQL 8.0 ou supérieur
- Maven 3.8 ou supérieur
- GPU NVIDIA avec CUDA (optionnel, recommandé pour les performances)

---

## Installation

### 1. Backend Spring Boot

```bash
git clone https://github.com/zeineb710/PCD_ecosurveillance.git
cd PCD_ecosurveillance/ecosurveillance-back
```

Configurer la base de données dans `src/main/resources/application.properties` :

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/ecosurveillance
spring.datasource.username=root
spring.datasource.password=TON_MOT_DE_PASSE
```

```bash
./mvnw spring-boot:run
```

Le serveur démarre sur `http://localhost:8081`.

---

### 2. Frontend Angular

```bash
cd PCD_ecosurveillance/ecosurveillance-front

npm install
ng serve
```

L'application démarre sur `http://localhost:4200`.

---

### 3. Module IA Python

```bash
cd PCD_ecosurveillance/ecosurveillance-ia
```

**Étape 1 — Télécharger le modèle YOLOv8**

Le fichier `best.pt` n'est pas inclus dans le repo (trop volumineux pour GitHub).

Télécharge-le ici : [best.pt — Google Drive](https://drive.google.com/drive/folders/1rt0yxxTblgmCWV9f9SiM0Mwx87SZr-9Q?usp=sharing)

Place-le dans :
```
ecosurveillance-ia/detection_aoi/best.pt
```

**Étape 2 — Installer PyTorch selon ton matériel :**

```bash
# CPU uniquement
pip install torch torchvision torchaudio

# GPU NVIDIA CUDA 12.8 (RTX 40xx / 50xx)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# GPU NVIDIA CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Étape 3 — Installer les dépendances :**

```bash
pip install -r requirements.txt
```

**Étape 4 — Configurer les chemins dans `detection_aoi/detection_v5.py` :**

```python
MODEL_DETECTION_PATH = "chemin/vers/best.pt"   # chemin vers le modèle téléchargé
VIDEO_SOURCE         = 0                        # 0 = webcam, ou chemin vers une vidéo
OUTPUT_DIR           = "chemin/vers/alertes"   # dossier de sauvegarde des captures et clips
```

> Exemple sur Windows :
> ```python
> MODEL_DETECTION_PATH = r"C:\Users\TonNom\Desktop\PCD_ecosurveillance\ecosurveillance-ia\detection_aoi\best.pt"
> OUTPUT_DIR           = r"C:\Users\TonNom\Desktop\alertes"
> ```

> Exemple sur Linux / macOS :
> ```python
> MODEL_DETECTION_PATH = "/home/tonnom/PCD_ecosurveillance/ecosurveillance-ia/detection_aoi/best.pt"
> OUTPUT_DIR           = "/home/tonnom/alertes"
> ```

**Étape 5 — Configurer la base de données dans `face_detection/reconnaissance_faciale_v2.py` :**

```python
DB_CONFIG = {
    "host"    : "localhost",
    "port"    : 3306,
    "user"    : "root",
    "password": "TON_MOT_DE_PASSE",
    "database": "ecosurveillance"
}
```

**Étape 6 — Lancer la détection :**

```bash
python detection_aoi/detection_v5.py
```

---

## Configuration

### Base de données MySQL

```sql
CREATE DATABASE ecosurveillance;
```

Le schéma est généré automatiquement par Spring Boot (Hibernate) au premier démarrage.

### Photos étudiants (reconnaissance faciale)

Placer les photos dans `ecosurveillance-ia/face_detection/photos_etudiants/` en respectant ce format de nom :

```
nom_prenom_annee_angle.jpg

Exemples :
  fouleni_foulen_2024_face.jpg
  fouleni_foulen_2024_gauche.jpg
```

Angles valides : `face`, `gauche`, `droite`, `pres`, `loin`, `haut`, `bas`

La matricule est générée automatiquement par le système au format `{id}INF{annee}`.

---

## Structure du projet

```
PCD_ecosurveillance/
│
├── ecosurveillance-back/                   ← Spring Boot (port 8081)
│   ├── src/
│   │   └── main/java/com/ecosurveillance/
│   │       ├── controller/
│   │       ├── service/
│   │       ├── entity/
│   │       ├── repository/
│   │       ├── dto/
│   │       ├── security/
│   │       └── enums/
│   ├── pom.xml
│   └── .gitignore
│
├── ecosurveillance-front/                  ← Angular 17 (port 4200)
│   ├── src/
│   │   └── app/
│   │       ├── components/
│   │       ├── pages/
│   │       ├── services/
│   │       ├── models/
│   │       ├── guards/
│   │       └── interceptors/
│   ├── angular.json
│   ├── package.json
│   └── .gitignore
│
├── ecosurveillance-ia/                     ← Pipeline IA Python
│   ├── detection_aoi/
│   │   ├── best.pt                         ← À télécharger séparément (Google Drive)
│   │   ├── detection_aoI.py                
│   │   └── detection_v5.py                 
│   ├── face_detection/
│   │   ├── photos_etudiants/               ← Photos au format nom_prenom_annee_angle.jpg
│   │   └── reconnaissance_faciale_v2.py    ← Module ArcFace
│   └── .gitignore
│
├── requirements.txt
└── README.md
```

