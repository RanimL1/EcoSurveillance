import cv2
import numpy as np
import torch
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from datetime import datetime
from collections import deque
import os
import sys
import threading
import queue
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'face_detection'))
from reconnaissance_faciale_v2 import (
    BaseDonnees, ReconnaissanceFaciale, traiter_alerte_avec_identification
)
import requests
import json



def _detecter_device():
    """Retourne 'cuda' si GPU disponible et fonctionnel, sinon 'cpu'."""
    if not torch.cuda.is_available():
        print("[INFO] ⚠️  CUDA non disponible → CPU (vérifier PyTorch cu128)")
        return "cpu"
    try:
        # Test rapide : alloue un petit tenseur sur GPU
        torch.zeros(1).cuda()
        nom = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"[INFO] ✅ GPU détecté : {nom} ({vram:.1f} GB VRAM)")
        return "cuda"
    except Exception as e:
        print(f"[INFO] ⚠️  GPU détecté mais inutilisable : {e} → CPU")
        return "cpu"

DEVICE     = _detecter_device()
USE_HALF   = (DEVICE == "cuda")   # FP16 seulement sur GPU


# =============================================================
# CONFIGURATION
# =============================================================

BACKEND_URL                = "http://localhost:8081/api"
BACKEND_DETECTION_ENDPOINT = f"{BACKEND_URL}/detections/python"

# Modèle entraîné sur les déchets à imgsz=1280
MODEL_DETECTION_PATH = model_path

# Modèle pose pré-entraîné Ultralytics (entraîné à 640)
MODEL_POSE_PATH = "yolov8n-pose.pt"

VIDEO_SOURCE = 0
OUTPUT_DIR   = your_dir

# Seuils de confiance
CONF_THRESH_DET  = 0.01
CONF_THRESH_POSE = 0.40

# FIX-2 : imgsz cohérent avec l'entraînement
IMGSZ_DET  = 1280   # cohérent avec l'entraînement du modèle déchets
IMGSZ_POSE = 640    # yolov8n-pose est pré-entraîné à 640

# ── COUCHE 1 : Keypoints ──────────────────────────────────────
SEUIL_POIGNET_NORM  = 0.25   # fraction hauteur personne
SEUIL_CONF_KEYPOINT = 0.30

# FIX-3 : fallback AOI v3 si keypoints absents
UPPER_BODY_RATIO_FALLBACK = 0.70   # 70% supérieur du corps
AOI_RATIO_SEUIL_FALLBACK  = 0.30   # ratio surface déchet dans upper body

# ── COUCHE 2 : Trajectoire ────────────────────────────────────
FENETRE_TRAJECTOIRE = 10
SEUIL_VECTEUR_Y     = 1.5
SEUIL_MAGNITUDE     = 2.0


SEUIL_ACCELERATION  = 0.3    # delta_magnitude minimal pour confirmer jet

# ── COUCHE 3 : Score de confiance ─────────────────────────────
SEUIL_CONFIANCE_JET     = 0.55
FRAMES_GRACE            = 4
FACTEUR_RELACHE         = 2
SEUIL_CONFIANCE_RELACHE = 0.35
COOLDOWN_FRAMES         = 90

# Cache keypoints
KP_CACHE_FRAMES  = 5


POSE_SKIP_FRAMES = 1

# ── Préexistence déchets ──────────────────────────────────────
DEPLACEMENT_REACTIVATION = 8
SEUIL_IMMOBILE           = 10

# ── Buffers vidéo ─────────────────────────────────────────────
BUFFER_AVANT = 60
BUFFER_APRES = 40

# ── Backend retry ─────────────────────────────────────────────
RETRY_MAX   = 3
RETRY_DELAI = 5

RECONNAISSANCE_ACTIVE = True

# ── Couleurs affichage ────────────────────────────────────────
COULEUR_PERSON   = (255, 100,   0)
COULEUR_TRASH    = (  0, 100, 255)
COULEUR_ALERTE   = (  0, 255,   0)
COULEUR_TENU     = (  0, 255, 255)
COULEUR_INACTIF  = (128, 128, 128)
COULEUR_POIGNET  = (255,   0, 255)
COULEUR_VECTEUR  = (255, 200,   0)
COULEUR_FALLBACK = (  0, 200, 255)   # upper body fallback AOI v3

# Indices keypoints COCO
KP_POIGNET_GAUCHE = 9
KP_POIGNET_DROIT  = 10
KP_EPAULE_GAUCHE  = 5
KP_EPAULE_DROIT   = 6
KP_HANCHE_GAUCHE  = 11
KP_HANCHE_DROIT   = 12


# =============================================================
# FILE D'ATTENTE BACKEND — envoi asynchrone avec retry
# =============================================================

_file_backend = queue.Queue()


def _worker_backend():
    """Thread daemon : consomme la file et envoie au backend avec retry."""
    while True:
        item = _file_backend.get()
        if item is None:
            break
        track_id, capture_path, clip_path, bbox_person, user_id, tentative = item
        succes = _envoyer_une_fois(track_id, capture_path, clip_path,
                                   bbox_person, user_id)
        if not succes and tentative < RETRY_MAX:
            print(f"[BACKEND] ⏳ Retry {tentative+1}/{RETRY_MAX} "
                  f"dans {RETRY_DELAI}s — ID={track_id}")
            time.sleep(RETRY_DELAI)
            _file_backend.put((track_id, capture_path, clip_path,
                               bbox_person, user_id, tentative + 1))
        elif not succes:
            print(f"[BACKEND] ❌ Abandon après {RETRY_MAX} tentatives "
                  f"— ID={track_id}")
        _file_backend.task_done()


def _envoyer_une_fois(track_id, capture_path, clip_path, bbox_person, user_id):
    """Envoie une alerte au backend. Retourne True si succès."""
    photo_handle = None
    video_handle = None
    try:
        data = {
            "type"           : "littering",
            "trackId"        : str(track_id),
            "bboxCoordinates": json.dumps(bbox_person),
        }
        if user_id:
            data["userId"] = str(user_id)

        files = {}
        if capture_path and os.path.exists(capture_path):
            photo_handle = open(capture_path, "rb")
            files["photo"] = (
                os.path.basename(capture_path), photo_handle, "image/jpeg"
            )
        if clip_path and os.path.exists(clip_path):
            video_handle = open(clip_path, "rb")
            files["video"] = (
                os.path.basename(clip_path), video_handle, "video/mp4"
            )

        response = requests.post(
            BACKEND_DETECTION_ENDPOINT, data=data,
            files=files, timeout=10
        )
        if response.status_code == 200:
            print(f"[BACKEND] ✅ Envoyé — ID: {track_id}")
            return True
        else:
            print(f"[BACKEND] ❌ {response.status_code} — {response.text}")
            return False
    except Exception as e:
        print(f"[BACKEND] ❌ Exception: {e}")
        return False
    finally:
        if photo_handle:
            photo_handle.close()
        if video_handle:
            video_handle.close()


def envoyer_detection_backend(track_id, capture_path, clip_path,
                               bbox_person, user_id=None):
    """Empile l'alerte dans la file (non bloquant)."""
    _file_backend.put((track_id, capture_path, clip_path,
                       bbox_person, user_id, 1))


# =============================================================
# FIX-3 — FALLBACK AOI v3 (upper body fixe)
# Utilisé quand keypoints=None (pose rate la personne)
# =============================================================

def _get_upper_body_bbox(bbox_person, ratio=UPPER_BODY_RATIO_FALLBACK):
    """Retourne les RATIO% supérieurs du bounding box personne."""
    x1, y1, x2, y2 = bbox_person
    return [x1, y1, x2, y1 + (y2 - y1) * ratio]


def _calculer_aoi(bbox1, bbox2):
    """Surface d'intersection entre deux bboxes."""
    x_min = max(bbox1[0], bbox2[0])
    y_min = max(bbox1[1], bbox2[1])
    x_max = min(bbox1[2], bbox2[2])
    y_max = min(bbox1[3], bbox2[3])
    return max(0, x_max - x_min) * max(0, y_max - y_min)


def trash_dans_upper_body_fallback(bbox_person, bbox_trash):
    """
    FIX-3 : fallback AOI v3.
    Retourne (dans_zone: bool, ratio: float).
    Utilisé quand les keypoints sont absents.
    """
    ub   = _get_upper_body_bbox(bbox_person)
    aire = (bbox_trash[2] - bbox_trash[0]) * (bbox_trash[3] - bbox_trash[1])
    if aire <= 0:
        return False, 0.0
    ratio = _calculer_aoi(ub, bbox_trash) / aire
    return ratio >= AOI_RATIO_SEUIL_FALLBACK, ratio


# =============================================================
# COUCHE 1 — KEYPOINTS : distance poignet ↔ déchet
# =============================================================

def extraire_keypoints_personne(result_pose, bbox_person):
    """
    Associe les keypoints YOLOv8-pose à une bbox_person.
    Retourne le tableau keypoints (17×3 : x, y, conf) ou None.
    """
    if result_pose is None or result_pose.keypoints is None:
        return None

    kps_data = result_pose.keypoints.data  # Tensor (N, 17, 3)
    boxes    = result_pose.boxes.xyxy      # Tensor (N, 4)

    if len(kps_data) == 0:
        return None

    cx_p = (bbox_person[0] + bbox_person[2]) / 2
    cy_p = (bbox_person[1] + bbox_person[3]) / 2
    hauteur_bbox   = max(bbox_person[3] - bbox_person[1], 1.0)
    tolerance_norm = 0.50 * hauteur_bbox

    meilleur_idx   = None
    meilleure_dist = float("inf")

    for i, box in enumerate(boxes):
        cx = float((box[0] + box[2]) / 2)
        cy = float((box[1] + box[3]) / 2)
        dist = ((cx - cx_p) ** 2 + (cy - cy_p) ** 2) ** 0.5
        if dist < meilleure_dist:
            meilleure_dist = dist
            meilleur_idx   = i

    if meilleure_dist > tolerance_norm or meilleur_idx is None:
        return None

    return kps_data[meilleur_idx].cpu().numpy()  # (17, 3)


def hauteur_personne_normalisee(keypoints, bbox_person):
    """
    Hauteur de référence pour normaliser les distances.
    Priorité : épaule↔hanche via keypoints. Fallback : bbox height.
    """
    if keypoints is not None:
        ep_g = keypoints[KP_EPAULE_GAUCHE]
        ep_d = keypoints[KP_EPAULE_DROIT]
        ha_g = keypoints[KP_HANCHE_GAUCHE]
        ha_d = keypoints[KP_HANCHE_DROIT]

        pts_valides = [kp for kp in [ep_g, ep_d, ha_g, ha_d]
                       if kp[2] >= SEUIL_CONF_KEYPOINT]

        if len(pts_valides) >= 2:
            ys = [p[1] for p in pts_valides]
            hauteur_tronc = max(ys) - min(ys)
            if hauteur_tronc > 10:
                return hauteur_tronc * 2.0

    h = bbox_person[3] - bbox_person[1]
    return max(h, 1.0)


def distance_poignet_dechet(keypoints, bbox_trash, hauteur_ref):
    """
    Retourne (distance_normalisee_min: float, poignet_coords: tuple|None).
    Retourne (inf, None) si keypoints=None ou aucun poignet fiable.
    """
    cx_t = (bbox_trash[0] + bbox_trash[2]) / 2
    cy_t = (bbox_trash[1] + bbox_trash[3]) / 2

    dist_min    = float("inf")
    poignet_ret = None

    if keypoints is None:
        return dist_min, poignet_ret

    for idx in [KP_POIGNET_GAUCHE, KP_POIGNET_DROIT]:
        kp = keypoints[idx]
        if kp[2] < SEUIL_CONF_KEYPOINT:
            continue
        dx        = float(kp[0]) - cx_t
        dy        = float(kp[1]) - cy_t
        dist_norm = (dx ** 2 + dy ** 2) ** 0.5 / hauteur_ref
        if dist_norm < dist_min:
            dist_min    = dist_norm
            poignet_ret = (float(kp[0]), float(kp[1]))

    return dist_min, poignet_ret


# =============================================================
# COUCHE 2 — TRAJECTOIRE : vecteur + accélération
# =============================================================

class HistoriqueTrajectoire:
    """
    Historique glissant des centroïdes pour calculer
    le vecteur de déplacement moyen et l'accélération.
    """

    def __init__(self):
        self.historiques = {}

    def ajouter(self, trash_id, bbox_trash):
        cx = (bbox_trash[0] + bbox_trash[2]) / 2
        cy = (bbox_trash[1] + bbox_trash[3]) / 2
        if trash_id not in self.historiques:
            self.historiques[trash_id] = deque(maxlen=FENETRE_TRAJECTOIRE)
        self.historiques[trash_id].append((cx, cy))

    def vecteur_moyen(self, trash_id):
        hist = self.historiques.get(trash_id)
        if hist is None or len(hist) < 2:
            return 0.0, 0.0, 0.0
        pts = list(hist)
        dxs = [pts[i+1][0] - pts[i][0] for i in range(len(pts)-1)]
        dys = [pts[i+1][1] - pts[i][1] for i in range(len(pts)-1)]
        vx  = sum(dxs) / len(dxs)
        vy  = sum(dys) / len(dys)
        return vx, vy, (vx**2 + vy**2) ** 0.5

    def acceleration(self, trash_id):
        """
        Variation de magnitude entre la 1ère et la 2ème moitié.
        Jet   → accélération positive (magnitude croissante).
        Dépôt → décélération négative (la main ralentit).
        """
        hist = self.historiques.get(trash_id)
        if hist is None or len(hist) < 4:
            return 0.0

        pts = list(hist)
        mid = len(pts) // 2

        def mag_segment(seg):
            dxs = [seg[i+1][0]-seg[i][0] for i in range(len(seg)-1)]
            dys = [seg[i+1][1]-seg[i][1] for i in range(len(seg)-1)]
            if not dxs:
                return 0.0
            vx = sum(dxs)/len(dxs)
            vy = sum(dys)/len(dys)
            return (vx**2 + vy**2) ** 0.5

        return mag_segment(pts[mid:]) - mag_segment(pts[:mid])

    def trajectoire_coherente(self, trash_id):
        """
        FIX-5 : seuil accélération durci à SEUIL_ACCELERATION (0.5).
        True si chute (vy≥seuil, mag≥seuil) ET accélération≥0.5.
        Distingue réellement jet (accélération) vs dépôt (décélération).
        """
        vx, vy, mag = self.vecteur_moyen(trash_id)
        accel       = self.acceleration(trash_id)
        return (vy  >= SEUIL_VECTEUR_Y
                and mag   >= SEUIL_MAGNITUDE
                and accel >= SEUIL_ACCELERATION)

    def dernier_point(self, trash_id):
        hist = self.historiques.get(trash_id)
        return hist[-1] if hist else None

    def nettoyer(self, ids_actifs):
        for tid in list(self.historiques.keys()):
            if tid not in ids_actifs:
                del self.historiques[tid]


# =============================================================
# GESTIONNAIRE DE DÉCHETS — logique contextuelle de préexistence
# =============================================================

class GestionnaireDechets:
    """
    Préexistant = immobile depuis > SEUIL_IMMOBILE frames.
    Réactivé    = préexistant qui se déplace > DEPLACEMENT_REACTIVATION px.
    """

    def __init__(self):
        self.dechets = {}

    def mettre_a_jour(self, trash_id, bbox_trash):
        cx = (bbox_trash[0] + bbox_trash[2]) / 2
        cy = (bbox_trash[1] + bbox_trash[3]) / 2

        if trash_id not in self.dechets:
            self.dechets[trash_id] = {
                "frames_visible"   : 0,
                "position_derniere": (cx, cy),
                "frames_immobile"  : 0,
                "preexistant"      : False,
                "reactivé"         : False,
            }

        etat = self.dechets[trash_id]
        etat["frames_visible"] += 1

        px, py      = etat["position_derniere"]
        deplacement = ((cx-px)**2 + (cy-py)**2) ** 0.5
        etat["position_derniere"] = (cx, cy)

        if deplacement < DEPLACEMENT_REACTIVATION:
            etat["frames_immobile"] += 1
        else:
            if etat["preexistant"]:
                etat["reactivé"]    = True
                etat["preexistant"] = False
                print(f"[DEBUG] Déchet #{trash_id} réactivé "
                      f"(dépl={deplacement:.1f}px)")
            etat["frames_immobile"] = 0

        if etat["frames_immobile"] > SEUIL_IMMOBILE and not etat["reactivé"]:
            etat["preexistant"] = True

    def est_preexistant(self, trash_id):
        if trash_id not in self.dechets:
            return False
        e = self.dechets[trash_id]
        return e["preexistant"] and not e["reactivé"]

    def nettoyer(self, ids_actifs):
        for tid in list(self.dechets.keys()):
            if tid not in ids_actifs:
                del self.dechets[tid]


# =============================================================
# ASSIGNATION GLOBALE DÉCHET ↔ PERSONNE (par frame) — v4.2
# FIX-3 intégré : fallback AOI v3 si keypoints absents
# =============================================================

def calculer_assignations(tracks_confirmes, bboxes_trash_avec_id,
                           gest_dechets, map_keypoints):
    """
    Pour chaque déchet non préexistant, trouve la personne dont
    le poignet est le plus proche (distance normalisée minimale).
    FIX-3 : si keypoints=None, utilise le ratio upper_body (AOI v3)
    comme distance proxy → évite l'exclusion silencieuse.
    Retourne {trash_id: (track_id, dist_norm)}.
    """
    assignations = {}

    for trash_id, bbox_trash in bboxes_trash_avec_id:
        if gest_dechets.est_preexistant(trash_id):
            continue

        meilleure_dist = float("inf")
        meilleur_id    = None

        for track_id, bbox_person in tracks_confirmes:
            keypoints = map_keypoints.get(track_id)
            hauteur   = hauteur_personne_normalisee(keypoints, bbox_person)

            if keypoints is not None:
                dist_norm, _ = distance_poignet_dechet(keypoints, bbox_trash,
                                                        hauteur)
            else:
                # FIX-3 : fallback AOI v3 — convertit le ratio en distance
                # proxy (ratio élevé = déchet proche → distance faible)
                _, ratio  = trash_dans_upper_body_fallback(bbox_person,
                                                            bbox_trash)
                # ratio ∈ [0,1] → dist_proxy ∈ [inf, 0] mappé sur [0, seuil]
                dist_norm = SEUIL_POIGNET_NORM * (1.0 - ratio) if ratio > 0 \
                            else float("inf")

            if dist_norm < meilleure_dist:
                meilleure_dist = dist_norm
                meilleur_id    = track_id

        if meilleur_id is not None and meilleure_dist <= SEUIL_POIGNET_NORM:
            assignations[trash_id] = (meilleur_id, meilleure_dist)

    return assignations


# =============================================================
# COUCHE 3 — SCORE DE CONFIANCE COMBINÉ
# =============================================================

def calculer_score_confiance(dist_norm, trajectoire_coherente):
    """
    Score ∈ [0, 1] combinant distance poignet et trajectoire.
    Score poignet normalisé sur [SEUIL_POIGNET_NORM, 3×seuil].
    Bonus 0.4 si trajectoire cohérente (FIX-5 : accél≥0.5 requis).
    """
    plage         = SEUIL_POIGNET_NORM * 2.0
    score_poignet = min(1.0, (dist_norm - SEUIL_POIGNET_NORM) / plage)
    score_traj    = 0.4 if trajectoire_coherente else 0.0
    return min(1.0, score_poignet * 0.6 + score_traj)


# =============================================================
# GESTIONNAIRE AOI v4.2 — trois couches + fallback AOI v3
# =============================================================

class GestionnaireAOI:
    """
    Détecte un jet en trois phases :
      1. Déchet assigné à la personne via keypoints OU upper_body
         (FIX-3 : fallback automatique si keypoints absents)
      2. Déchet lâché : distance > seuil pendant FRAMES_GRACE
         ET trajectoire cohérente (accel ≥ 0.5 — FIX-5)
      3. Score de confiance combiné > SEUIL_CONFIANCE_JET
    """

    def __init__(self, frames_grace=FRAMES_GRACE):
        self.frames_grace = frames_grace
        self.etats        = {}

    def mettre_a_jour(self, track_id, bbox_person, keypoints,
                      bboxes_trash_avec_id, gest_dechets,
                      assignations_globales, hist_trajectoire):
        """
        Retourne (jet_detecte: bool, bbox_trash_jet, score: float).
        """
        if track_id not in self.etats:
            self.etats[track_id] = {
                "tenait_dechet"      : False,
                "frames_sans_dechet" : 0,
                "bbox_trash_derniere": None,
                "trash_id_tenu"      : None,
                "cooldown"           : 0,
                "score_courant"      : 0.0,
                "poignet_coords"     : None,
                "mode_fallback"      : False,
            }

        etat = self.etats[track_id]

        if etat["cooldown"] > 0:
            etat["cooldown"] -= 1
            return False, None, 0.0

        hauteur_ref = hauteur_personne_normalisee(keypoints, bbox_person)
        mode_fallback = (keypoints is None)

        # ── Trouver le déchet assigné à cette personne ──────────
        meilleure_dist       = float("inf")
        meilleure_trash_bbox = None
        meilleur_trash_id    = None
        meilleur_poignet     = None

        for trash_id, bbox_trash in bboxes_trash_avec_id:
            if gest_dechets.est_preexistant(trash_id):
                continue
            if trash_id in assignations_globales:
                owner, _ = assignations_globales[trash_id]
                if owner != track_id:
                    continue

            if not mode_fallback:
                # Couche 1 normale : distance poignet
                dist_norm, poignet = distance_poignet_dechet(
                    keypoints, bbox_trash, hauteur_ref
                )
            else:
                # FIX-3 : fallback AOI v3
                _, ratio  = trash_dans_upper_body_fallback(bbox_person,
                                                            bbox_trash)
                dist_norm = SEUIL_POIGNET_NORM * (1.0 - ratio) if ratio > 0 \
                            else float("inf")
                poignet   = None

            if dist_norm < meilleure_dist:
                meilleure_dist       = dist_norm
                meilleure_trash_bbox = bbox_trash
                meilleur_trash_id    = trash_id
                meilleur_poignet     = poignet

        etat["poignet_coords"] = meilleur_poignet
        etat["mode_fallback"]  = mode_fallback

        # ── Couche 1 : déchet tenu ? ────────────────────────────
        if meilleure_dist <= SEUIL_POIGNET_NORM:
            etat["tenait_dechet"]       = True
            etat["frames_sans_dechet"]  = 0
            etat["bbox_trash_derniere"] = meilleure_trash_bbox
            etat["trash_id_tenu"]       = meilleur_trash_id
            etat["score_courant"]       = 0.0
            return False, None, 0.0

        # ── Couche 2 + 3 : lâcher en cours ? ──────────────────
        elif etat["tenait_dechet"]:
            etat["frames_sans_dechet"] += 1

            trash_id_ref = etat["trash_id_tenu"]
            traj_ok = (
                hist_trajectoire.trajectoire_coherente(trash_id_ref)
                if trash_id_ref is not None else False
            )

            score = calculer_score_confiance(meilleure_dist, traj_ok)
            etat["score_courant"] = score

            fb_tag = "[FALLBACK]" if mode_fallback else ""
            print(f"[DEBUG]{fb_tag} ID={track_id} "
                  f"| absence={etat['frames_sans_dechet']}f "
                  f"| dist={meilleure_dist:.2f} | traj={traj_ok} "
                  f"| score={score:.2f}")

            condition_normale = (etat["frames_sans_dechet"] >= self.frames_grace
                                 and score >= SEUIL_CONFIANCE_JET)
            condition_relache = (
                etat["frames_sans_dechet"] >= self.frames_grace * FACTEUR_RELACHE
                and score >= SEUIL_CONFIANCE_RELACHE
            )

            if condition_normale or condition_relache:
                raison = "normal" if condition_normale else "relâché"
                print(f"[DEBUG] ✅ Jet confirmé ID={track_id} "
                      f"| score={score:.2f} | mode={raison}{fb_tag}")
                bbox_jet = etat["bbox_trash_derniere"]
                etat["tenait_dechet"]       = False
                etat["frames_sans_dechet"]  = 0
                etat["cooldown"]            = COOLDOWN_FRAMES
                etat["score_courant"]       = 0.0
                return True, bbox_jet, score

        return False, None, etat.get("score_courant", 0.0)

    def supprimer_track(self, track_id):
        if track_id in self.etats:
            del self.etats[track_id]


# =============================================================
# SAUVEGARDE
# =============================================================

def yolo_vers_deepsort(detection):
    x1, y1, x2, y2, conf, cls = detection
    return ([x1, y1, x2 - x1, y2 - y1], conf, int(cls))


def sauvegarder_alerte(frame, track_id, bbox_person, bbox_trash,
                        keypoints=None, score=0.0, mode_fallback=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom = f"{OUTPUT_DIR}/alerte_ID{track_id}_{ts}.jpg"
    img = frame.copy()

    x1, y1, x2, y2 = [int(v) for v in bbox_person]
    cv2.rectangle(img, (x1, y1), (x2, y2), COULEUR_ALERTE, 3)
    label_mode = " [UB]" if mode_fallback else ""
    cv2.putText(img, f"JETEUR ID={track_id} score={score:.2f}{label_mode}",
                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, COULEUR_ALERTE, 2)

    if mode_fallback:
        ub = _get_upper_body_bbox([x1, y1, x2, y2])
        cv2.rectangle(img, (int(ub[0]), int(ub[1])),
                      (int(ub[2]), int(ub[3])), COULEUR_FALLBACK, 1)
    elif keypoints is not None:
        for idx in [KP_POIGNET_GAUCHE, KP_POIGNET_DROIT]:
            kp = keypoints[idx]
            if kp[2] >= SEUIL_CONF_KEYPOINT:
                cv2.circle(img, (int(kp[0]), int(kp[1])),
                           6, COULEUR_POIGNET, -1)

    if bbox_trash:
        tx1, ty1, tx2, ty2 = [int(v) for v in bbox_trash]
        cv2.rectangle(img, (tx1, ty1), (tx2, ty2), COULEUR_TRASH, 2)
        cv2.putText(img, "DECHET JETE", (tx1, ty1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COULEUR_TRASH, 2)

    cv2.putText(img, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(nom, img)
    print(f"[ALERTE] Capture : {nom}")
    return nom



def sauvegarder_clip_video(frames_avant, frames_apres, track_id, fps=20):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    toutes = frames_avant + frames_apres
    if not toutes:
        return None

    h, w = toutes[0].shape[:2]

    nom_temp  = f"{OUTPUT_DIR}/temp_ID{track_id}_{ts}.mp4"
    nom_final = f"{OUTPUT_DIR}/clip_ID{track_id}_{ts}.mp4"

    writer = cv2.VideoWriter(nom_temp, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    if not writer.isOpened():
        print("[ALERTE] ❌ Impossible de créer le clip")
        return None
    for f in toutes:
        writer.write(f)
    writer.release()

    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-i", nom_temp,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        nom_final
    ]
    result = subprocess.run(cmd, capture_output=True)

    if os.path.exists(nom_temp):
        os.remove(nom_temp)

    if os.path.exists(nom_final):
        print(f"[ALERTE] Clip : {nom_final}")
        return nom_final
    else:
        print(f"[ALERTE] ❌ FFmpeg échoué : {result.stderr.decode()}")
        return None
# =============================================================
# WORKER RECONNAISSANCE FACIALE — thread asynchrone
# =============================================================

_file_reconnaissance = queue.Queue()


def _worker_reconnaissance(recog, db):
    """Thread daemon : traite chaque alerte en arrière-plan."""
    while True:
        item = _file_reconnaissance.get()
        if item is None:
            break
        (frame_copy, track_id, bbox_person,
         capture_path, frames_avant, frames_apres) = item

        try:
            resultat = traiter_alerte_avec_identification(
                frame        = frame_copy,
                track_id     = track_id,
                bbox_person  = bbox_person,
                recog        = recog,
                db           = db,
                capture_path = capture_path or ""
            )
        except Exception as e:
            print(f"[RECOG] ❌ Erreur : {e}")
            resultat = None

        user_id = None
        if resultat and resultat.get("etudiant"):
            user_id = resultat["etudiant"]["etudiant_id"]
            print(f"[RECOG] ✅ "
                  f"{resultat['etudiant']['prenom']} "
                  f"{resultat['etudiant']['nom']}")

        clip_path = sauvegarder_clip_video(frames_avant, frames_apres, track_id)
        envoyer_detection_backend(track_id, capture_path, clip_path,
                                  bbox_person, user_id)
        _file_reconnaissance.task_done()


# =============================================================
# FUSION DÉTECTIONS PERSONNES (pose ∪ det)
# =============================================================

def _iou(b1, b2):
    xi1 = max(b1[0], b2[0]); yi1 = max(b1[1], b2[1])
    xi2 = min(b1[2], b2[2]); yi2 = min(b1[3], b2[3])
    inter = max(0, xi2-xi1) * max(0, yi2-yi1)
    if inter == 0:
        return 0.0
    aire1 = (b1[2]-b1[0]) * (b1[3]-b1[1])
    aire2 = (b2[2]-b2[0]) * (b2[3]-b2[1])
    return inter / (aire1 + aire2 - inter)


def fusionner_detections_personnes(det_pose, det_fallback, seuil_iou=0.50):
    """
    Union de det_pose et det_fallback.
    Une détection fallback est ajoutée uniquement si IoU < seuil_iou
    avec toutes les détections pose (évite les doublons).
    """
    fusion = list(det_pose)
    for d_fb in det_fallback:
        bb_fb = d_fb[:4]
        chevauchement = any(_iou(bb_fb, d_p[:4]) >= seuil_iou
                            for d_p in det_pose)
        if not chevauchement:
            fusion.append(d_fb)
    return fusion


# =============================================================
# CACHE KEYPOINTS TEMPOREL
# =============================================================

class CacheKeypoints:
    """
    Conserve les derniers keypoints valides pendant KP_CACHE_FRAMES
    frames pour absorber les occlusions courtes.
    """

    def __init__(self, ttl=KP_CACHE_FRAMES):
        self.ttl    = ttl
        self._cache = {}

    def mettre_a_jour(self, track_id, kps):
        if kps is not None:
            self._cache[track_id] = {"kps": kps, "age": 0}
            return kps
        entree = self._cache.get(track_id)
        if entree is None:
            return None
        entree["age"] += 1
        if entree["age"] > self.ttl:
            del self._cache[track_id]
            return None
        return entree["kps"]

    def nettoyer(self, ids_actifs):
        for tid in list(self._cache.keys()):
            if tid not in ids_actifs:
                del self._cache[tid]


# =============================================================
# BOUCLE PRINCIPALE
# =============================================================

def lancer_detection():
    global RECONNAISSANCE_ACTIVE

    threading.Thread(target=_worker_backend, daemon=True).start()

    # ── FIX-1 : Chargement modèles sur GPU ──────────────────────
    # NE PAS appeler .half() manuellement : Ultralytics fuse() les
    # couches Conv+BN au chargement et échoue si le modèle est déjà
    # en FP16. Le FP16 est activé via le paramètre half= à l'inférence.
    print(f"[INFO] Chargement modèle déchets sur {DEVICE} "
          f"(imgsz={IMGSZ_DET}, half={USE_HALF})...")
    model_det = YOLO(MODEL_DETECTION_PATH)

    print(f"[INFO] Chargement modèle pose sur {DEVICE} "
          f"(imgsz={IMGSZ_POSE}, half={USE_HALF})...")
    model_pose = YOLO(MODEL_POSE_PATH)

    tracker_personnes = DeepSort(max_age=30, n_init=3, max_iou_distance=0.7)
    tracker_dechets   = DeepSort(max_age=60, n_init=2, max_iou_distance=0.7)

    gestionnaire   = GestionnaireAOI()
    gest_dechets   = GestionnaireDechets()
    hist_traj      = HistoriqueTrajectoire()
    cache_kp       = CacheKeypoints()
    compteur_frame = 0

    db    = None
    recog = None
    if RECONNAISSANCE_ACTIVE:
        try:
            db    = BaseDonnees()
            recog = ReconnaissanceFaciale(db)
            threading.Thread(
                target=_worker_reconnaissance,
                args=(recog, db),
                daemon=True
            ).start()
            print("[INFO] ✅ Reconnaissance faciale (thread).")
        except Exception as e:
            print(f"[INFO] ⚠️  Reconnaissance désactivée : {e}")
            RECONNAISSANCE_ACTIVE = False

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("[ERREUR] Impossible d'ouvrir la source vidéo.")
        return

    alertes_totales    = 0
    frames_buffer      = []
    alertes_en_attente = {}

    # ── FIX-4 : Premier appel pose RÉEL pour initialiser res_pose ──
    ret_init, frame_init = cap.read()
    if frame_init is not None:
        res_pose = model_pose(
            frame_init, conf=CONF_THRESH_POSE,
            imgsz=IMGSZ_POSE, device=DEVICE,
            half=USE_HALF, verbose=False
        )[0]
        frames_buffer.append(frame_init.copy())
    else:
        res_pose = None

    print(f"[INFO] Démarrage v4.2 | device={DEVICE} | half={USE_HALF} | "
          f"det_imgsz={IMGSZ_DET} | pose_imgsz={IMGSZ_POSE} | "
          f"pose_skip={POSE_SKIP_FRAMES} | "
          f"accel_seuil={SEUIL_ACCELERATION} | "
          f"buffer={BUFFER_AVANT}+{BUFFER_APRES}f")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        frames_buffer.append(frame.copy())
        if len(frames_buffer) > BUFFER_AVANT:
            frames_buffer.pop(0)

        # ── Alimenter les buffers post-alerte ───────────────────
        for tid in list(alertes_en_attente.keys()):
            info = alertes_en_attente[tid]
            info["frames_apres"].append(frame.copy())
            info["compteur_apres"] += 1
            if info["compteur_apres"] >= BUFFER_APRES:
                _file_reconnaissance.put((
                    info["frame_alerte"],
                    tid,
                    info["bbox_person"],
                    info["capture_path"],
                    info["frames_avant"],
                    info["frames_apres"],
                ))
                del alertes_en_attente[tid]

        # ----------------------------------------------------------
        # ÉTAPE 1 : Détection déchets — FIX-1+2 : GPU + imgsz=1280
        # ----------------------------------------------------------
        res_det = model_det(
            frame, conf=CONF_THRESH_DET,
            imgsz=IMGSZ_DET, device=DEVICE,
            half=USE_HALF, verbose=False
        )[0]

        detections_person_fallback = []
        detections_trash           = []

        for det in res_det.boxes.data.tolist():
            x1, y1, x2, y2, conf, cls = det
            cls = int(cls)
            if cls == 0:
                detections_person_fallback.append(det)
            elif cls == 1:
                detections_trash.append(det)

        # ----------------------------------------------------------
        # ÉTAPE 2 : Détection pose — FIX-1+4 : GPU + init correcte
        # ----------------------------------------------------------
        compteur_frame += 1
        executer_pose  = (compteur_frame % max(1, POSE_SKIP_FRAMES) == 0)

        if executer_pose:
            res_pose = model_pose(
                frame, conf=CONF_THRESH_POSE,
                imgsz=IMGSZ_POSE, device=DEVICE,
                half=USE_HALF, verbose=False
            )[0]

        detections_person_pose = []
        if res_pose is not None and res_pose.boxes is not None:
            for det in res_pose.boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = det
                detections_person_pose.append([x1, y1, x2, y2, conf, 0])

        detections_person = fusionner_detections_personnes(
            detections_person_pose, detections_person_fallback
        )

        # ----------------------------------------------------------
        # ÉTAPE 3 : Tracking
        # ----------------------------------------------------------
        tracks_personnes = tracker_personnes.update_tracks(
            [yolo_vers_deepsort(d) for d in detections_person], frame=frame
        )
        tracks_dechets = tracker_dechets.update_tracks(
            [yolo_vers_deepsort(d) for d in detections_trash], frame=frame
        )

        # ----------------------------------------------------------
        # ÉTAPE 4 : Mise à jour gestionnaire déchets + trajectoires
        # ----------------------------------------------------------
        bboxes_trash_avec_id = []
        ids_dechets_actifs   = set()

        for track in tracks_dechets:
            if not track.is_confirmed():
                continue
            tid  = track.track_id
            ltrb = track.to_ltrb()
            bbox = [ltrb[0], ltrb[1], ltrb[2], ltrb[3]]
            ids_dechets_actifs.add(tid)
            bboxes_trash_avec_id.append((tid, bbox))
            gest_dechets.mettre_a_jour(tid, bbox)
            hist_traj.ajouter(tid, bbox)

        gest_dechets.nettoyer(ids_dechets_actifs)
        hist_traj.nettoyer(ids_dechets_actifs)

        # ----------------------------------------------------------
        # ÉTAPE 5 : Extraction keypoints par personne trackée
        # ----------------------------------------------------------
        tracks_confirmes      = []
        map_keypoints         = {}
        ids_personnes_actives = set()

        for track in tracks_personnes:
            if not track.is_confirmed():
                continue
            ltrb        = track.to_ltrb()
            bbox_person = [ltrb[0], ltrb[1], ltrb[2], ltrb[3]]
            tid         = track.track_id
            tracks_confirmes.append((tid, bbox_person))
            ids_personnes_actives.add(tid)

            kps_frais = (
                extraire_keypoints_personne(res_pose, bbox_person)
                if (executer_pose and res_pose is not None) else None
            )
            kps = cache_kp.mettre_a_jour(tid, kps_frais)
            map_keypoints[tid] = kps

        cache_kp.nettoyer(ids_personnes_actives)

        # ----------------------------------------------------------
        # ÉTAPE 6 : Assignation globale — FIX-3 : fallback intégré
        # ----------------------------------------------------------
        assignations = calculer_assignations(
            tracks_confirmes, bboxes_trash_avec_id,
            gest_dechets, map_keypoints
        )

        # ----------------------------------------------------------
        # ÉTAPE 7 : Logique AOI v4.2 + Dessin
        # ----------------------------------------------------------
        ids_actifs = set()

        for track_id, bbox_person in tracks_confirmes:
            ids_actifs.add(track_id)
            keypoints     = map_keypoints.get(track_id)
            mode_fallback = (keypoints is None)

            jet_detecte, bbox_trash_jet, score = gestionnaire.mettre_a_jour(
                track_id              = track_id,
                bbox_person           = bbox_person,
                keypoints             = keypoints,
                bboxes_trash_avec_id  = bboxes_trash_avec_id,
                gest_dechets          = gest_dechets,
                assignations_globales = assignations,
                hist_trajectoire      = hist_traj,
            )

            x1, y1, x2, y2 = [int(v) for v in bbox_person]
            couleur = COULEUR_ALERTE if jet_detecte else COULEUR_PERSON
            cv2.rectangle(frame, (x1, y1), (x2, y2), couleur, 2)
            cv2.putText(frame, f"ID={track_id}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, couleur, 2)

            if mode_fallback:
                # Afficher le upper body fallback en cyan
                ub = _get_upper_body_bbox([x1, y1, x2, y2])
                cv2.rectangle(frame,
                              (int(ub[0]), int(ub[1])),
                              (int(ub[2]), int(ub[3])),
                              COULEUR_FALLBACK, 1)
                cv2.putText(frame, "UB", (x1, y2 + 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            COULEUR_FALLBACK, 1)
            elif keypoints is not None:
                for idx in [KP_POIGNET_GAUCHE, KP_POIGNET_DROIT]:
                    kp = keypoints[idx]
                    if kp[2] >= SEUIL_CONF_KEYPOINT:
                        cv2.circle(frame, (int(kp[0]), int(kp[1])),
                                   5, COULEUR_POIGNET, -1)

            score_courant = gestionnaire.etats.get(
                track_id, {}
            ).get("score_courant", 0.0)
            if score_courant > 0.1:
                cv2.putText(frame, f"sc={score_courant:.2f}",
                            (x1, y2 + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (200, 200, 200), 1)

            if jet_detecte:
                alertes_totales += 1
                print(f"[ALERTE] Jet détecté ! ID={track_id} "
                      f"| score={score:.2f} "
                      f"| fallback={mode_fallback}")

                capture_path = None
                if bbox_trash_jet:
                    capture_path = sauvegarder_alerte(
                        frame, track_id, bbox_person, bbox_trash_jet,
                        keypoints, score, mode_fallback
                    )

                cv2.putText(
                    frame,
                    f"! JET DETECTE ID={track_id} score={score:.2f} !",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, COULEUR_ALERTE, 3
                )

                if RECONNAISSANCE_ACTIVE and recog is not None:
                    # FIX-6 : ne pas écraser une alerte déjà en attente
                    if track_id not in alertes_en_attente:
                        alertes_en_attente[track_id] = {
                            "frame_alerte"  : frame.copy(),
                            "bbox_person"   : bbox_person,
                            "capture_path"  : capture_path,
                            "frames_avant"  : list(frames_buffer),
                            "frames_apres"  : [],
                            "compteur_apres": 0,
                        }
                    else:
                        print(f"[ALERTE] ⚠️  ID={track_id} déjà en attente "
                              f"— alerte ignorée (COOLDOWN insuffisant ?)")
                else:
                    clip_path = sauvegarder_clip_video(
                        list(frames_buffer), [], track_id
                    )
                    envoyer_detection_backend(
                        track_id, capture_path, clip_path, bbox_person
                    )

        # ── Dessiner les déchets + vecteur trajectoire ──────────
        for trash_id, bbox_t in bboxes_trash_avec_id:
            tx1, ty1, tx2, ty2 = [int(v) for v in bbox_t]

            if trash_id in assignations:
                couleur_t = COULEUR_TENU
                label     = f"TENU#{trash_id}"
            elif gest_dechets.est_preexistant(trash_id):
                couleur_t = COULEUR_INACTIF
                label     = "sol"
            else:
                couleur_t = COULEUR_TRASH
                label     = f"trash#{trash_id}"

            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), couleur_t, 2)
            cv2.putText(frame, label, (tx1, ty1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, couleur_t, 1)

            vx, vy, mag = hist_traj.vecteur_moyen(trash_id)
            if mag > 1.0:
                cx = int((tx1 + tx2) / 2)
                cy = int((ty1 + ty2) / 2)
                cv2.arrowedLine(
                    frame, (cx, cy),
                    (int(cx + vx * 5), int(cy + vy * 5)),
                    COULEUR_VECTEUR, 2, tipLength=0.4
                )

        # ── Nettoyage tracks inactifs ────────────────────────────
        for tid in set(gestionnaire.etats.keys()) - ids_actifs:
            gestionnaire.supprimer_track(tid)

        # ── HUD ─────────────────────────────────────────────────
        cv2.putText(frame, f"Alertes: {alertes_totales}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame,
                    f"v4.2 | {DEVICE.upper()} | det={IMGSZ_DET} "
                    f"| half={USE_HALF}",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("Detection v4.2 - Jet de déchets", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # ── Arrêt propre ─────────────────────────────────────────────
    _file_reconnaissance.put(None)
    _file_backend.put(None)

    if db is not None:
        db.fermer()
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[INFO] Terminé. Total alertes : {alertes_totales}")


# =============================================================
# POINT D'ENTRÉE
# =============================================================

if __name__ == "__main__":
    lancer_detection()