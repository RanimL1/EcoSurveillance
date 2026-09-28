"""
=============================================================
  Module de Reconnaissance Faciale — Faculté ENSI
  Outils   : OpenCV + DeepFace (ArcFace) + MySQL
  Version  : multi-photos par étudiant
=============================================================

"""
import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
from deepface import DeepFace
import os
import json
from datetime import datetime
import bcrypt

# =============================================================
# CONFIGURATION — À MODIFIER SELON TON ENVIRONNEMENT
# =============================================================

DB_CONFIG = {
    "host"    : "localhost",
    "port"    : 3306,
    "user"    : "root",
    "password": "TON_MOT_DE_PASSE",   
    "database": "ecosurveillance"
}

MODELE_FACIAL     = "ArcFace"         # modèle de reconnaissance
BACKEND_DETECTEUR = "opencv"          # détecteur de visages
SEUIL_SIMILARITE  = 0.85              # distance cosinus max (0=identique, 1=différent)

DOSSIER_PHOTOS    = r"C:\Users\GIGABYTE\Desktop\liaison\detection_main\face_detection\photos_etudiants"  # dossier contenant les photos
DOSSIER_TEMP      = "temp_faces"        # dossier temporaire (créé automatiquement)
ANGLES_VALIDES = [
    "face",       # face frontale
    "gauche",     # légèrement à gauche
    "droite",     # légèrement à droite
    "pres",       # photo de près (gros plan)
    "loin",       # photo de loin
    "haut",       # angle caméra en hauteur (comme une vraie caméra de surveillance)
    "bas"
]

CASCADE_PATH      = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"



def parser_nom_fichier(nom_fichier):
    base  = os.path.splitext(nom_fichier)[0]
    parts = base.split("_")

    if len(parts) < 4:
        print(f"[PARSE] ⚠️  Nom invalide : '{nom_fichier}'")
        print(f"         Format attendu : nom_prenom_annee_angle.jpg")
        return None

    nom    = parts[0].capitalize()
    prenom = parts[1].capitalize()
    annee  = parts[2]
    angle  = parts[-1].lower()

    if angle not in ANGLES_VALIDES:
        print(f"[PARSE] ⚠️  Angle invalide '{angle}' dans '{nom_fichier}'")
        return None

    return {
        "nom"   : nom,
        "prenom": prenom,
        "annee" : annee,
        "angle" : angle
    }

class BaseDonnees:
    """
    Gère toutes les opérations MySQL pour ECO Surveillance.
    Adapté pour la structure Spring Boot (tables: users, detections, infractions, face_vectors)
    """

    def __init__(self):
        self.connexion = None
        self._connecter()

    def _connecter(self):
        try:
            self.connexion = mysql.connector.connect(**DB_CONFIG)
            if self.connexion.is_connected():
                print("[DB] ✅ Connexion MySQL réussie.")
                # Créer les tables si elles n'existent pas
                self._creer_tables_si_necessaire()
        except Error as e:
            print(f"[DB] ❌ Connexion échouée : {e}")
            raise

    def fermer(self):
        if self.connexion and self.connexion.is_connected():
            self.connexion.close()
            print("[DB] Connexion fermée.")

    def _creer_tables_si_necessaire(self):
        """Crée les tables nécessaires si elles n'existent pas"""
        cursor = self.connexion.cursor()
        
        # Table face_vectors si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_vectors (
                id INT PRIMARY KEY AUTO_INCREMENT,
                vector TEXT NOT NULL,
                user_id INT UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Ajouter la colonne track_id à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN track_id INT
            """)
        except:
            pass  # La colonne existe déjà
            
        # Ajouter la colonne capture_path à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN capture_path VARCHAR(255)
            """)
        except:
            pass
            
        # Ajouter la colonne bbox_coordinates à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN bbox_coordinates TEXT
            """)
        except:
            pass
            
        # Ajouter la colonne detection_id à infractions si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE infractions ADD COLUMN detection_id INT,
                ADD FOREIGN KEY (detection_id) REFERENCES detections(id)
            """)
        except:
            pass
            
        self.connexion.commit()
        cursor.close()


    def etudiant_existe(self, nom, prenom):
        cursor = self.connexion.cursor()
        cursor.execute(
            "SELECT id, matricule FROM users WHERE nom = %s AND prenom = %s",
            (nom, prenom)
        )
        result = cursor.fetchone()
        cursor.close()
        return result  # retourne (id, matricule) ou None


    def creer_etudiant(self, nom, prenom, annee):
        existant = self.etudiant_existe(nom, prenom)
        if existant:
            return existant[0]  # retourne l'id

        try:
            cursor = self.connexion.cursor()
            email = f"{prenom.lower()}.{nom.lower()}@ecosurveillance.com"
            mot_de_passe_clair = f"{nom.lower()}{annee}"
            mot_de_passe_hashe = bcrypt.hashpw(
                mot_de_passe_clair.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # Insertion sans matricule d'abord
            cursor.execute("""
                INSERT INTO users (nom, prenom, email, password, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (nom, prenom, email, mot_de_passe_hashe, "ETUDIANT"))
            self.connexion.commit()
            etudiant_id = cursor.lastrowid

            # Génération et mise à jour de la matricule avec l'ID réel
            matricule = f"{etudiant_id}INF{annee}"
            cursor.execute(
                "UPDATE users SET matricule = %s WHERE id = %s",
                (matricule, etudiant_id)
            )
            self.connexion.commit()
            cursor.close()

            print(f"[DB] 👤 Étudiant créé : {prenom} {nom} → ID={etudiant_id}, matricule={matricule}")
            return etudiant_id

        except Error as e:
            print(f"[DB] ❌ Erreur création étudiant : {e}")
            return None

    # ----------------------------------------------------------
    # Gestion des vecteurs faciaux (table face_vectors)
    # ----------------------------------------------------------

    def ajouter_vecteur_facial(self, user_id, embedding):
        
        try:
            embedding_json = json.dumps(embedding)
            cursor = self.connexion.cursor()
            # Toujours insérer une nouvelle ligne (pas de UNIQUE sur user_id)
            cursor.execute("""
                INSERT INTO face_vectors (user_id, vector)
                VALUES (%s, %s)
            """, (user_id, embedding_json))
            self.connexion.commit()
            cursor.close()
            print(f"[DB]    ✅ Vecteur facial ajouté pour user_id={user_id}")
            return True
        except Error as e:
            print(f"[DB] ❌ Erreur ajout vecteur facial : {e}")
            return False

    # ----------------------------------------------------------
    # Chargement des embeddings pour la reconnaissance
    # ----------------------------------------------------------

    def charger_tous_embeddings(self):
        """
        Charge tous les vecteurs faciaux depuis MySQL.
        """
        cursor = self.connexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                u.id        AS etudiant_id,
                u.nom,
                u.prenom,
                u.matricule,
                fv.vector   AS embedding
            FROM face_vectors fv
            JOIN users u ON fv.user_id = u.id
            WHERE fv.vector IS NOT NULL
        """)
        rows = cursor.fetchall()
        cursor.close()

        for row in rows:
            row["embedding"] = json.loads(row["embedding"])
            row["filiere"] = "Informatique"  # Valeur par défaut

        nb_etudiants = len(set(r["etudiant_id"] for r in rows))
        print(f"[DB] 📦 {len(rows)} vecteurs faciaux chargés pour {nb_etudiants} étudiants.")
        return rows

    # ----------------------------------------------------------
    # Gestion des détections (table detections)
    # ----------------------------------------------------------

    def enregistrer_detection(self, user_id, track_id, capture_path, bbox_coordinates):
        """
        Enregistre une détection dans la table detections.
        """
        try:
            cursor = self.connexion.cursor()
            cursor.execute("""
                INSERT INTO detections (type, detected_at, confirmed, track_id, capture_path, bbox_coordinates, user_id)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, ("littering", False, track_id, capture_path, bbox_coordinates, user_id))
            self.connexion.commit()
            detection_id = cursor.lastrowid
            cursor.close()
            print(f"[DB] 🚨 Détection #{detection_id} enregistrée (user_id={user_id}, track_id={track_id})")
            return detection_id

        except Error as e:
            print(f"[DB] ❌ Erreur enregistrement détection : {e}")
            return None

    # ----------------------------------------------------------
    # Créer une infraction automatiquement
    # ----------------------------------------------------------

    def creer_infraction(self, user_id, detection_id, description, preuve_url):
        """
        Crée une infraction liée à une détection.
        """
        try:
            cursor = self.connexion.cursor()
            cursor.execute("""
                INSERT INTO infractions (etudiant_id, description, created_at, infraction_date, status, preuve_url, detection_id)
                VALUES (%s, %s, NOW(), NOW(), %s, %s, %s)
            """, (user_id, description, "EN_ATTENTE", preuve_url, detection_id))
            self.connexion.commit()
            infraction_id = cursor.lastrowid
            cursor.close()
            print(f"[DB] 📝 Infraction #{infraction_id} créée pour détection #{detection_id}")
            return infraction_id

        except Error as e:
            print(f"[DB] ❌ Erreur création infraction : {e}")
            return None


# =============================================================
# CLASSE : Insertion des étudiants depuis un dossier de photos
# =============================================================

class InserteurPhotos:
    """
    Parcourt un dossier de photos, parse les noms de fichiers,
    calcule les embeddings ArcFace et insère tout dans MySQL.

    Format du nom de fichier :
        nom_prenom_matricule_filiere_angle.jpg
    """

    def __init__(self, db: BaseDonnees):
        self.db = db
        os.makedirs(DOSSIER_TEMP, exist_ok=True)

    
    def calculer_embedding(self, chemin_photo):
        try:
            resultat = DeepFace.represent(
                img_path          = chemin_photo,
                model_name        = MODELE_FACIAL,
                detector_backend  = "retinaface",  
                enforce_detection = False           
            )
            # Vérifier quand même qu'un visage a été trouvé
            if not resultat or resultat[0].get("face_confidence", 1) < 0.5:
                print(f"[EMBED] ⚠️  Visage peu fiable dans '{chemin_photo}' — ignoré")
                return None
            return resultat[0]["embedding"]
        except Exception as e:
            print(f"[EMBED] ❌ Impossible de calculer l'embedding pour '{chemin_photo}' : {e}")
            return None

    def inserer_depuis_dossier(self, dossier=DOSSIER_PHOTOS):
        if not os.path.exists(dossier):
            print(f"[INSERT] ❌ Dossier introuvable : '{dossier}'")
            print(f"          Crée le dossier et place tes photos dedans.")
            return 0

        extensions = [".jpg", ".jpeg", ".png"]
        photos = [
            f for f in os.listdir(dossier)
            if os.path.splitext(f)[1].lower() in extensions
        ]

        if not photos:
            print(f"[INSERT] ⚠️  Aucune photo trouvée dans '{dossier}'")
            return 0

        print(f"\n[INSERT] 📂 {len(photos)} photo(s) trouvée(s) dans '{dossier}'")
        print("=" * 60)

        succes   = 0
        echecs   = 0

        for nom_fichier in sorted(photos):
            chemin_complet = os.path.join(dossier, nom_fichier)
            print(f"\n[INSERT] 🖼️  Traitement : {nom_fichier}")

            # 1. Parser le nom du fichier
            infos = parser_nom_fichier(nom_fichier)
            if infos is None:
                echecs += 1
                continue

            etudiant_id = self.db.creer_etudiant(
                nom    = infos["nom"],
                prenom = infos["prenom"],
                annee  = infos["annee"]
            )
            if etudiant_id is None:
                echecs += 1
                continue

            # 3. Calculer l'embedding
            print(f"[INSERT]    Calcul de l'embedding ArcFace...")
            embedding = self.calculer_embedding(chemin_complet)
            if embedding is None:
                echecs += 1
                continue

            # 4. Insérer la photo dans la base
            ok = self.db.ajouter_vecteur_facial(
                user_id   = etudiant_id,
                embedding = embedding
            )
            if ok:
                succes += 1
            else:
                echecs += 1

        print("\n" + "=" * 60)
        print(f"[INSERT] ✅ Succès : {succes} photos")
        print(f"[INSERT] ❌ Échecs : {echecs} photos")
        return succes


# =============================================================
# CLASSE : Reconnaissance faciale en temps réel
# =============================================================

class ReconnaissanceFaciale:
    """
    Identifie les visages dans une frame vidéo en 3 étapes :
      1. Haar Cascade (OpenCV) → détection rapide des visages
      2. ArcFace (DeepFace)    → extraction de l'embedding
      3. Distance cosinus      → comparaison avec la base MySQL
    """

    def __init__(self, db: BaseDonnees):
        self.db = db
        self.detecteur_haar = cv2.CascadeClassifier(CASCADE_PATH)
        self.etudiants_db   = self.db.charger_tous_embeddings()
        os.makedirs(DOSSIER_TEMP, exist_ok=True)
        print(f"[FACIAL] ✅ Module initialisé avec {len(self.etudiants_db)} embeddings.")

    def recharger_base(self):
        """Recharge les embeddings depuis MySQL (utile si la base a changé)."""
        self.etudiants_db = self.db.charger_tous_embeddings()
        print(f"[FACIAL] 🔄 Base rechargée : {len(self.etudiants_db)} embeddings.")

    # ----------------------------------------------------------
    # Détection Haar Cascade
    # ----------------------------------------------------------

    def detecter_visages_haar(self, frame):
        """
        Détection rapide des visages avec Haar Cascade.
        Retourne une liste de (x, y, w, h).
        """
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        visages = self.detecteur_haar.detectMultiScale(
            gris,
            scaleFactor  = 1.1,
            minNeighbors = 5,
            minSize      = (60, 60)
        )
        return visages if len(visages) > 0 else []

    # ----------------------------------------------------------
    # Extraction d'embedding ArcFace
    # ----------------------------------------------------------

    def extraire_embedding(self, frame, x, y, w, h):
        """
        Extrait l'embedding ArcFace d'un visage détecté.
        Retourne la liste de 512 floats ou None.
        """
        try:
            # Recadrer le visage avec une marge
            marge = 10
            x1 = max(0, x - marge)
            y1 = max(0, y - marge)
            x2 = min(frame.shape[1], x + w + marge)
            y2 = min(frame.shape[0], y + h + marge)
            visage_crop = frame[y1:y2, x1:x2]

            if visage_crop.size == 0:
                return None

            # Sauvegarder temporairement pour DeepFace
            chemin_temp = os.path.join(DOSSIER_TEMP, "temp_face.jpg")
            cv2.imwrite(chemin_temp, visage_crop)

            # Extraction ArcFace (Haar a déjà localisé le visage)
            resultat = DeepFace.represent(
                img_path         = chemin_temp,
                model_name       = MODELE_FACIAL,
                detector_backend = "skip",
                enforce_detection= False
            )
            return resultat[0]["embedding"]

        except Exception:
            return None

    # ----------------------------------------------------------
    # Distance cosinus
    # ----------------------------------------------------------

    def distance_cosinus(self, emb1, emb2):
        
        v1 = np.array(emb1)
        v2 = np.array(emb2)
        cosinus = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
        return 1.0 - cosinus

    

    def identifier_visage(self, embedding_inconnu):
        if not self.etudiants_db or embedding_inconnu is None:
            return None, float('inf')

        # Regrouper par etudiant_id, garder la meilleure distance
        meilleurs = {}

        for row in self.etudiants_db:
            eid      = row["etudiant_id"]
            distance = self.distance_cosinus(embedding_inconnu, row["embedding"])

            if eid not in meilleurs or distance < meilleurs[eid]["distance"]:
                meilleurs[eid] = {
                    "distance": distance,
                    "etudiant": row
                }

        if not meilleurs:
            return None, float('inf')

        # Trouver le meilleur étudiant parmi tous
        meilleur = min(meilleurs.values(), key=lambda x: x["distance"])

        if meilleur["distance"] <= SEUIL_SIMILARITE:
            return meilleur["etudiant"], meilleur["distance"]
        else:
            return None, meilleur["distance"]

    # ----------------------------------------------------------
    # Analyse complète d'une frame
    # ----------------------------------------------------------

    def analyser_frame(self, frame):
        """
        Analyse une frame complète :
          1. Détecte tous les visages
          2. Extrait leur embedding
          3. Identifie chaque visage

        Retourne une liste de dicts :
        [{"bbox": (x,y,w,h), "etudiant": dict|None, "distance": float, "identifie": bool}]
        """
        resultats = []
        visages   = self.detecter_visages_haar(frame)

        for (x, y, w, h) in visages:
            embedding          = self.extraire_embedding(frame, x, y, w, h)
            etudiant, distance = self.identifier_visage(embedding)

            resultats.append({
                "bbox"     : (x, y, w, h),
                "etudiant" : etudiant,
                "distance" : distance,
                "identifie": etudiant is not None
            })

        return resultats

    # ----------------------------------------------------------
    # Affichage des résultats sur la frame
    # ----------------------------------------------------------

    def dessiner_resultats(self, frame, resultats):
        """
        Dessine les bounding boxes et labels sur la frame.
        Vert = identifié, Rouge = inconnu.
        """
        for res in resultats:
            x, y, w, h = res["bbox"]
            etudiant    = res["etudiant"]

            if res["identifie"]:
                couleur    = (0, 255, 0)
                label      = f"{etudiant['prenom']} {etudiant['nom']}"
                sous_label = f"{etudiant['matricule']} | {res['distance']:.2f}"  # ✅
            else:
                couleur    = (0, 0, 255)
                label      = "Inconnu"
                sous_label = f"dist={res['distance']:.2f}"

            cv2.rectangle(frame, (x, y), (x + w, y + h), couleur, 2)
            cv2.putText(frame, label,     (x, y - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, couleur, 2)
            cv2.putText(frame, sous_label,(x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, couleur, 1)

        return frame




def traiter_alerte_avec_identification(frame, track_id, bbox_person,
                                       recog: ReconnaissanceFaciale,
                                       db: BaseDonnees,
                                       capture_path: str):
    
    x1, y1, x2, y2 = [int(v) for v in bbox_person]
    region = frame[max(0, y1):y2, max(0, x1):x2]
    bbox_json = json.dumps(bbox_person)
    if region.size == 0:
        return None
    resultats_visages = recog.analyser_frame(region)
    etudiant_identifie = None
    for res in resultats_visages:
        if res["identifie"]:
            etudiant_identifie = res["etudiant"]
            break
    user_id = etudiant_identifie["etudiant_id"] if etudiant_identifie else None

    if etudiant_identifie:
        print(f"[ALERTE] 🎯 Identifié : {etudiant_identifie['prenom']} "
              f"{etudiant_identifie['nom']} ({etudiant_identifie['matricule']})")
    else:
        print(f"[ALERTE] ❓ Visage non identifié")

    return {
        "detection_id": None,
        "track_id": track_id,
        "etudiant": etudiant_identifie,
        "nb_visages_detectes": len(resultats_visages)
    }
# =============================================================
# POINT D'ENTRÉE — TEST STANDALONE
# =============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  ECO SURVEILLANCE — Module Reconnaissance Faciale")
    print("=" * 60)

    # 1. Connexion à la base de données
    db = BaseDonnees()

    # 2. Insérer les étudiants depuis le dossier de photos
    #    (à faire une seule fois, ou quand de nouvelles photos sont ajoutées)
    print(f"\n[MAIN] Insertion des photos depuis '{DOSSIER_PHOTOS}'...")
    inserteur = InserteurPhotos(db)
    inserteur.inserer_depuis_dossier(DOSSIER_PHOTOS)

    # 3. Initialiser le module de reconnaissance
    print("\n[MAIN] Initialisation de la reconnaissance faciale...")
    recog = ReconnaissanceFaciale(db)

    # 4. Test en temps réel avec la webcam
    print("\n[MAIN] Ouverture de la webcam...")
    print("[MAIN] Appuie sur 'q' pour quitter, 'r' pour recharger la base.\n")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[MAIN] ❌ Impossible d'ouvrir la webcam.")
    else:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Analyser et afficher les résultats
            resultats = recog.analyser_frame(frame)
            frame     = recog.dessiner_resultats(frame, resultats)

            # Afficher le nombre de visages détectés
            cv2.putText(frame, f"Visages: {len(resultats)}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Reconnaissance Faciale — ECO Surveillance ENSI", frame)

            touche = cv2.waitKey(1) & 0xFF
            if touche == ord('q'):
                break
            elif touche == ord('r'):
                recog.recharger_base()

        cap.release()
        cv2.destroyAllWindows()

    db.fermer()
    print("\n[MAIN] Programme terminé.")