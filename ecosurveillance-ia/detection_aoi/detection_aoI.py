"""
=============================================================
  Système de détection de jet de déchets — Faculté ENSI
  Pipeline : YOLOv8 + DeepSORT + Logique AOI
=============================================================
"""

import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from datetime import datetime
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'face_detection'))
from reconnaissance_faciale_v2 import BaseDonnees, ReconnaissanceFaciale, traiter_alerte_avec_identification
import requests
import json

# Configuration du backend Spring Boot
BACKEND_URL = "http://localhost:8081/api"
BACKEND_DETECTION_ENDPOINT = f"{BACKEND_URL}/detections/python"
# =============================================================
# CONFIGURATION
# =============================================================

MODEL_PATH    = model_path        # ton modèle YOLOv8 entraîné
VIDEO_SOURCE  = 0             # 0 = webcam, ou chemin vers une vidéo
OUTPUT_DIR    = "alertes"         # dossier de sauvegarde des captures
CONF_THRESH   = 0.05    # seuil de confiance YOLO
AOI_SEUIL     = 50                # aire minimale d'intersection pour considérer "en main"
FRAMES_GRACE  = 10          # nombre de frames pour confirmer un jet
RECONNAISSANCE_ACTIVE = True   # passer à False pour désactiver
COOLDOWN_FRAMES = 90 
# Classes de ton modèle (dans l'ordre de l'entraînement)
CLASSES = {0: "person", 1: "trash"}

# Couleurs d'affichage
COULEUR_PERSON = (255, 100, 0)    # bleu
COULEUR_TRASH  = (0, 100, 255)    # rouge/orange
COULEUR_ALERTE = (0, 255, 0)      # vert


# =============================================================
# FONCTION : Calcul de l'AOI entre deux bounding boxes
# =============================================================

def calculer_aoi(bbox1, bbox2):
    """
    Calcule l'aire d'intersection entre deux bounding boxes.

    Paramètres :
        bbox1 : [x1, y1, x2, y2]
        bbox2 : [x1, y1, x2, y2]

    Retourne :
        aire de l'intersection (0 si pas de chevauchement)
    """
    x_inter_min = max(bbox1[0], bbox2[0])
    y_inter_min = max(bbox1[1], bbox2[1])
    x_inter_max = min(bbox1[2], bbox2[2])
    y_inter_max = min(bbox1[3], bbox2[3])

    largeur  = max(0, x_inter_max - x_inter_min)
    hauteur  = max(0, y_inter_max - y_inter_min)

    return largeur * hauteur


# =============================================================
# FONCTION : Convertir détection YOLO → format DeepSORT
# =============================================================

def yolo_vers_deepsort(detection):
    """
    Convertit une détection YOLO au format attendu par DeepSORT.
    YOLO donne [x1, y1, x2, y2, conf, classe]
    DeepSORT attend ([left, top, width, height], conf, classe)
    """
    x1, y1, x2, y2, conf, cls = detection
    left   = x1
    top    = y1
    width  = x2 - x1
    height = y2 - y1
    return ([left, top, width, height], conf, int(cls))


# =============================================================
# FONCTION : Sauvegarder une capture d'alerte
# =============================================================

def sauvegarder_alerte(frame, track_id, bbox_person, bbox_trash):
    """
    Sauvegarde une image d'alerte avec les bounding boxes tracées.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"{OUTPUT_DIR}/alerte_ID{track_id}_{horodatage}.jpg"

    frame_alerte = frame.copy()

    # Dessiner bbox personne
    x1, y1, x2, y2 = [int(v) for v in bbox_person]
    cv2.rectangle(frame_alerte, (x1, y1), (x2, y2), COULEUR_ALERTE, 3)
    cv2.putText(frame_alerte, f"JETEUR ID={track_id}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COULEUR_ALERTE, 2)

    # Dessiner bbox déchet
    tx1, ty1, tx2, ty2 = [int(v) for v in bbox_trash]
    cv2.rectangle(frame_alerte, (tx1, ty1), (tx2, ty2), COULEUR_TRASH, 2)
    cv2.putText(frame_alerte, "DECHET JETE", (tx1, ty1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COULEUR_TRASH, 2)

    # Ajouter horodatage
    cv2.putText(frame_alerte, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imwrite(nom_fichier, frame_alerte)
    print(f"[ALERTE] Capture sauvegardée : {nom_fichier}")
    return nom_fichier

def sauvegarder_clip_video(frames_buffer, track_id, fps=20):
    """
    Sauvegarde un clip vidéo à partir d'un buffer de frames.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"{OUTPUT_DIR}/clip_ID{track_id}_{horodatage}.mp4"

    if not frames_buffer:
        return None

    h, w = frames_buffer[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(nom_fichier, fourcc, fps, (w, h))
    for f in frames_buffer:
        writer.write(f)
    writer.release()
    print(f"[ALERTE] Clip vidéo sauvegardé : {nom_fichier}")
    return nom_fichier



def envoyer_detection_backend(track_id, capture_path, clip_path, bbox_person, user_id=None):
    """
    Envoie photo + vidéo en multipart/form-data au backend.
    """
    try:
        data = {
            "type": "littering",
            "trackId": str(track_id),
            "bboxCoordinates": json.dumps(bbox_person)
        }
        if user_id:
            data["userId"] = str(user_id)

        files = {}
        if capture_path and os.path.exists(capture_path):
            files["photo"] = (os.path.basename(capture_path), open(capture_path, "rb"), "image/jpeg")
        if clip_path and os.path.exists(clip_path):
            files["video"] = (os.path.basename(clip_path), open(clip_path, "rb"), "video/mp4")

        response = requests.post(BACKEND_DETECTION_ENDPOINT, data=data, files=files)

        if response.status_code == 200:
            print(f"[BACKEND] ✅ Envoyé - ID: {track_id}")
            return response.json()
        else:
            print(f"[BACKEND] ❌ {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[BACKEND] ❌ Erreur: {e}")
        return None
# =============================================================
# CLASSE PRINCIPALE : Gestionnaire d'état AOI par personne
# =============================================================

class GestionnaireAOI:
    """
    Suit l'état AOI pour chaque personne trackée.

    Pour chaque ID de personne, on mémorise :
    - si elle tenait un déchet (aoi_precedente > seuil)
    - depuis combien de frames le déchet est sorti de sa zone
    """

    def __init__(self, seuil=AOI_SEUIL, frames_grace=FRAMES_GRACE):
        self.seuil        = seuil
        self.frames_grace = frames_grace

        # {track_id: {"tenait_dechet": bool, "frames_sans_dechet": int, "bbox_trash_derniere": bbox}}
        self.etats = {}

        

    def mettre_a_jour(self, track_id, bbox_person, bboxes_trash):
        """
        Met à jour l'état AOI pour une personne donnée.

        Retourne True si un jet de déchet est détecté.
        """
        # Initialiser l'état si première fois
        if track_id not in self.etats:
            self.etats[track_id] = {
                "tenait_dechet"      : False,
                "frames_sans_dechet" : 0,
                "bbox_trash_derniere": None,
                "cooldown"           : 0 

            }

        etat = self.etats[track_id]
        aoi_max = 0
        meilleure_trash_bbox = None
        if etat["cooldown"] > 0:
            etat["cooldown"] -= 1
            return False, None
        # Calculer l'AOI avec tous les déchets détectés dans la frame
        for bbox_trash in bboxes_trash:
            aoi = calculer_aoi(bbox_person, bbox_trash)
            if aoi > aoi_max:
                aoi_max = aoi
                meilleure_trash_bbox = bbox_trash

        # Mise à jour de l'état
        if aoi_max > self.seuil:
            # Le déchet est dans la zone de la personne → elle tient quelque chose
            etat["tenait_dechet"]       = True
            etat["frames_sans_dechet"]  = 0
            etat["bbox_trash_derniere"] = meilleure_trash_bbox

        elif etat["tenait_dechet"]:
            # Elle tenait un déchet, maintenant AOI = 0 → elle l'a peut-être jeté
            etat["frames_sans_dechet"] += 1

            # Confirmer après N frames sans déchet (évite les faux positifs)
            if etat["frames_sans_dechet"] >= self.frames_grace:
                # JET DÉTECTÉ
                etat["tenait_dechet"]      = False
                etat["frames_sans_dechet"] = 0
                etat["cooldown"]           = COOLDOWN_FRAMES
                return True, etat["bbox_trash_derniere"]

        return False, None

    def supprimer_track(self, track_id):
        """Nettoyer les tracks qui ne sont plus actifs."""
        if track_id in self.etats:
            del self.etats[track_id]


# =============================================================
# BOUCLE PRINCIPALE
# =============================================================

def lancer_detection():
    global RECONNAISSANCE_ACTIVE

    # Chargement du modèle YOLOv8
    print("[INFO] Chargement du modèle YOLOv8...")
    model = YOLO(MODEL_PATH)

    # Initialisation de DeepSORT
    print("[INFO] Initialisation de DeepSORT...")
    tracker = DeepSort(
        max_age=30,           # garder un track N frames sans détection
        n_init=3,             # confirmer un track après N détections
        max_iou_distance=0.7
    )

    # Gestionnaire AOI
    gestionnaire = GestionnaireAOI()
    # ── AJOUT : Initialisation reconnaissance faciale ───────────
    db    = None
    recog = None
    if RECONNAISSANCE_ACTIVE:
        try:
            db    = BaseDonnees()
            recog = ReconnaissanceFaciale(db)
            print("[INFO] ✅ Reconnaissance faciale initialisée.")
        except Exception as e:
            print(f"[INFO] ⚠️  Reconnaissance désactivée : {e}")
            RECONNAISSANCE_ACTIVE = False
    
    # Ouverture de la source vidéo
    print(f"[INFO] Ouverture de la source vidéo : {VIDEO_SOURCE}")
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    if not cap.isOpened():
        print("[ERREUR] Impossible d'ouvrir la source vidéo.")
        return

    alertes_totales = 0

    print("[INFO] Démarrage de la détection. Appuie sur 'q' pour quitter.")
    BUFFER_SIZE = 60  # ~3 secondes à 20fps
    frames_buffer = []
    while True:
        ret, frame = cap.read()
        frames_buffer.append(frame.copy())
        if len(frames_buffer) > BUFFER_SIZE:
            frames_buffer.pop(0)
        if not ret:
            break

        # ----------------------------------------------------------
        # ÉTAPE 1 : Détection YOLO
        # ----------------------------------------------------------
        resultats = model(frame, conf=CONF_THRESH, verbose=False)[0]

        detections_person = []
        bboxes_trash_frame = []

        for det in resultats.boxes.data.tolist():
            x1, y1, x2, y2, conf, cls = det
            cls = int(cls)

            if cls == 0:  # person
                detections_person.append(det)
            elif cls == 1:  # trash
                bboxes_trash_frame.append([x1, y1, x2, y2])

        # ----------------------------------------------------------
        # ÉTAPE 2 : Tracking DeepSORT (sur les personnes uniquement)
        # ----------------------------------------------------------
        entrees_tracker = [yolo_vers_deepsort(d) for d in detections_person]
        tracks = tracker.update_tracks(entrees_tracker, frame=frame)

        # ----------------------------------------------------------
        # ÉTAPE 3 : Logique AOI + Dessin
        # ----------------------------------------------------------
        ids_actifs = set()

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ids_actifs.add(track_id)
            ltrb = track.to_ltrb()  # [left, top, right, bottom]
            bbox_person = [ltrb[0], ltrb[1], ltrb[2], ltrb[3]]

            # Vérification AOI
            jet_detecte, bbox_trash_jet = gestionnaire.mettre_a_jour(
                track_id, bbox_person, bboxes_trash_frame
            )

            # Affichage de la bbox personne
            x1, y1, x2, y2 = [int(v) for v in bbox_person]
            couleur = COULEUR_ALERTE if jet_detecte else COULEUR_PERSON
            cv2.rectangle(frame, (x1, y1), (x2, y2), couleur, 2)
            cv2.putText(frame, f"ID={track_id}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, couleur, 2)

            if jet_detecte:
                alertes_totales += 1
                print(f"[ALERTE] Jet détecté ! Personne ID={track_id}")

                # Sauvegarder la capture
                clip_path = sauvegarder_clip_video(list(frames_buffer), track_id)
                capture_path = None
                if bbox_trash_jet:
                    capture_path = sauvegarder_alerte(frame, track_id, bbox_person, bbox_trash_jet)

                user_id = None
                etudiant_info = None
                resultat = None
                # ── AJOUT : Reconnaissance faciale ──────────────────
                if RECONNAISSANCE_ACTIVE and recog is not None:
                    resultat=traiter_alerte_avec_identification(
                        frame        = frame,
                        track_id     = track_id,
                        bbox_person  = bbox_person,
                        recog        = recog,
                        db           = db,
                        capture_path = capture_path or ""
                    )
                    if resultat and resultat.get("etudiant"):
                        user_id = resultat["etudiant"]["etudiant_id"]
                        etudiant_info = resultat["etudiant"]
                    
                    envoyer_detection_backend(
                        track_id=track_id,
                        capture_path=capture_path,
                        clip_path=clip_path,
                        bbox_person=bbox_person,
                        user_id=user_id
                    )
                    
                    # Afficher bannière sur la frame
                    if etudiant_info:
                        cv2.putText(frame, f"! JET DETECTE - {etudiant_info['prenom']} {etudiant_info['nom']} !",
                                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COULEUR_ALERTE, 3)
                    else:
                        cv2.putText(frame, f"! JET DETECTE ID={track_id} !",
                                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COULEUR_ALERTE, 3)
                                # ────────────────────────────────────────────────────

                # Afficher bannière sur la frame
                cv2.putText(frame, f"! JET DETECTE ID={track_id} !",
                            (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                            COULEUR_ALERTE, 3)

        # Dessiner les bounding boxes des déchets
        for bbox_t in bboxes_trash_frame:
            tx1, ty1, tx2, ty2 = [int(v) for v in bbox_t]
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), COULEUR_TRASH, 2)
            cv2.putText(frame, "trash", (tx1, ty1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COULEUR_TRASH, 1)

        # Nettoyer les tracks inactifs
        ids_inactifs = set(gestionnaire.etats.keys()) - ids_actifs
        for tid in ids_inactifs:
            gestionnaire.supprimer_track(tid)

        # Compteur en haut à gauche
        cv2.putText(frame, f"Alertes: {alertes_totales}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # ----------------------------------------------------------
        # AFFICHAGE
        # ----------------------------------------------------------
        cv2.imshow("Detection - Jet de déchets", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # ── AJOUT : Fermer la connexion DB ───────────────────────────
    if db is not None:
        db.fermer()
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[INFO] Détection terminée. Total alertes : {alertes_totales}")


# =============================================================
# POINT D'ENTRÉE
# =============================================================

if __name__ == "__main__":
    lancer_detection()