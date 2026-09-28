package com.ecosurveillance.controller;

import com.ecosurveillance.dto.DetectionDTO;
import com.ecosurveillance.entity.Detection;
import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.entity.Preuve;
import com.ecosurveillance.repository.InfractionRepository;
import com.ecosurveillance.repository.PreuveRepository;
import com.ecosurveillance.service.DetectionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.multipart.MultipartFile;
import com.ecosurveillance.repository.DetectionRepository;

import java.io.IOException;
import java.nio.file.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/detections")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor


public class DetectionController {

    private final DetectionService detectionService;
    private final PreuveRepository preuveRepository;
    private final InfractionRepository infractionRepository;
    private final DetectionRepository detectionRepository;
    @Value("${preuves.storage.path}")
    private String storagePath;

    // ── Endpoint Python (multipart) ──────────────────────────────
    // @PostMapping(value = "/python", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    // public ResponseEntity<?> createDetectionFromPython(
    //         @RequestParam String type,
    //         @RequestParam String trackId,
    //         @RequestParam(required = false) String userId,
    //         @RequestParam(required = false) String bboxCoordinates,
    //         @RequestPart(required = false) MultipartFile photo,
    //         @RequestPart(required = false) MultipartFile video
    // ) {
    //     // 1. Créer la détection + infraction via service
    //     Detection detection = detectionService.createDetectionFromPython(
    //             type, trackId, userId, bboxCoordinates
    //     );

    //     // 2. Récupérer l'infraction liée à cette détection
    //     Infraction infraction = detection.getInfraction();

    //     if (infraction != null) {
    //         // 3. Sauvegarder fichiers + créer Preuve
    //         Preuve preuve = new Preuve();
    //         preuve.setInfraction(infraction);
    //         preuve.setImageUrl(sauvegarderFichier(photo));
    //         preuve.setVideoUrl(sauvegarderFichier(video));
    //         preuveRepository.save(preuve);
    //     }

    //     return ResponseEntity.ok(Map.of("status", "ok", "detectionId", detection.getId()));
    // }

    // @PostMapping(value = "/python", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    // public ResponseEntity<?> createDetectionFromPython(
    //         @RequestParam String type,
    //         @RequestParam String trackId,
    //         @RequestParam(required = false) String userId,
    //         @RequestParam(required = false) String bboxCoordinates,
    //         @RequestPart(required = false) MultipartFile photo,
    //         @RequestPart(required = false) MultipartFile video
    // ) {
    //     System.out.println("[DETECTION] Reçu - trackId=" + trackId + " userId=" + userId);
    //     System.out.println("[DETECTION] photo=" + (photo != null ? photo.getOriginalFilename() + " (" + photo.getSize() + " bytes)" : "null"));
    //     System.out.println("[DETECTION] video=" + (video != null ? video.getOriginalFilename() + " (" + video.getSize() + " bytes)" : "null"));
 
    //     Detection detection = detectionService.createDetectionFromPython(
    //             type, trackId, userId, bboxCoordinates
    //     );
 
    //     Infraction infraction = detection.getInfraction();
    //     System.out.println("[DETECTION] Infraction créée: " + (infraction != null ? infraction.getId() : "NULL"));
 
    //     if (infraction != null) {
    //         String imageUrl = sauvegarderFichier(photo);
    //         String videoUrl = sauvegarderFichier(video);
    //         System.out.println("[PREUVE] imageUrl=" + imageUrl);
    //         System.out.println("[PREUVE] videoUrl=" + videoUrl);
 
    //         if (imageUrl != null || videoUrl != null) {
    //             Preuve preuve = new Preuve();
    //             preuve.setInfraction(infraction);
    //             preuve.setImageUrl(imageUrl);
    //             preuve.setVideoUrl(videoUrl);
    //             Preuve saved = preuveRepository.save(preuve);
    //             System.out.println("[PREUVE] ✅ Sauvegardée en base - id=" + saved.getId());
    //         } else {
    //             System.out.println("[PREUVE] ⚠️ Aucun fichier reçu, preuve non créée");
    //         }
    //     }
 
    //     return ResponseEntity.ok(Map.of("status", "ok", "detectionId", detection.getId()));
    // }

    // @PostMapping(value = "/python", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    // public ResponseEntity<?> createDetectionFromPython(
    //         @RequestParam String type,
    //         @RequestParam String trackId,
    //         @RequestParam(required = false) String userId,
    //         @RequestParam(required = false) String bboxCoordinates,
    //         @RequestPart(required = false) MultipartFile photo,
    //         @RequestPart(required = false) MultipartFile video
    // ) {
    //     Detection detection = detectionService.createDetectionFromPython(
    //             type, trackId, userId, bboxCoordinates
    //     );

    //     Infraction infraction = detection.getInfraction();

    //     String imageUrl = sauvegarderFichier(photo);
    //     String videoUrl = sauvegarderFichier(video);

    //     if (infraction != null) {
    //         // ── Mettre à jour preuve_url sur l'infraction ──────────
    //         if (imageUrl != null) {
    //             infraction.setPreuveUrl(imageUrl);  // ← format cohérent avec l'ancien pipeline
    //             infractionRepository.save(infraction);            // ← persister
    //         }

    //         // ── Sauvegarder dans la table preuves aussi ────────────
    //         if (imageUrl != null || videoUrl != null) {
    //             Preuve preuve = new Preuve();
    //             preuve.setInfraction(infraction);
    //             if (imageUrl != null) preuve.setImageUrl("alertes/" + imageUrl);
    //             if (videoUrl != null) preuve.setVideoUrl("alertes/" + videoUrl);
    //             preuveRepository.save(preuve);
    //         }
    //     }

    //     return ResponseEntity.ok(Map.of("status", "ok", "detectionId", detection.getId()));
    // }

    // @PostMapping(value = "/python", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    // public ResponseEntity<?> createDetectionFromPython(
    //         @RequestParam String type,
    //         @RequestParam String trackId,
    //         @RequestParam(required = false) String userId,
    //         @RequestParam(required = false) String bboxCoordinates,
    //         @RequestPart(required = false) MultipartFile photo,
    //         @RequestPart(required = false) MultipartFile video
    // ) {
    //     Detection detection = detectionService.createDetectionFromPython(
    //             type, trackId, userId, bboxCoordinates
    //     );

    //     String imageUrl = sauvegarderFichier(photo);
    //     String videoUrl = sauvegarderFichier(video);

    //     // Toujours sauvegarder les chemins sur la détection
    //     if (imageUrl != null) detection.setCapturePath("alertes/" + imageUrl);
    //     if (videoUrl != null) detection.setVideoPath("alertes/" + videoUrl);
    //     detectionRepository.save(detection);

    //     // Si infraction existe → mettre à jour preuve_url
    //     Infraction infraction = detection.getInfraction();
    //     if (infraction != null) {
    //         if (imageUrl != null) infraction.setPreuveUrl("alertes/" + imageUrl);
    //         infractionRepository.save(infraction);
    //     }

    //     return ResponseEntity.ok(Map.of("status", "ok", "detectionId", detection.getId()));
    // }
    @PostMapping(value = "/python", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> createDetectionFromPython(
            @RequestParam String type,
            @RequestParam String trackId,
            @RequestParam(required = false) String userId,
            @RequestParam(required = false) String bboxCoordinates,
            @RequestPart(required = false) MultipartFile photo,
            @RequestPart(required = false) MultipartFile video
    ) {
        Detection detection = detectionService.createDetectionFromPython(
                type, trackId, userId, bboxCoordinates
        );

        String imageUrl = sauvegarderFichier(photo);
        String videoUrl = sauvegarderFichier(video);

        if (imageUrl != null) detection.setCapturePath("alertes/" + imageUrl);
        if (videoUrl != null) detection.setVideoPath("alertes/" + videoUrl);
        detectionRepository.save(detection);

        // Mettre à jour l'infraction avec detection_id + preuve_url
        Infraction infraction = detection.getInfraction();
        if (infraction != null) {
            infraction.setDetection(detection);   // ← lien manquant
            if (imageUrl != null) infraction.setPreuveUrl("alertes/" + imageUrl);
            infractionRepository.save(infraction);
        }

        return ResponseEntity.ok(Map.of("status", "ok", "detectionId", detection.getId()));
    }

    // ── Endpoints existants ──────────────────────────────────────
    @PostMapping
    public ResponseEntity<DetectionDTO> createDetection(@RequestBody DetectionDTO dto) {
        return ResponseEntity.ok(detectionService.createDetection(dto));
    }

    @GetMapping
    public ResponseEntity<List<DetectionDTO>> getAllDetections() {
        return ResponseEntity.ok(detectionService.getAllDetections());
    }

    @PutMapping("/{id}/confirm")
    public ResponseEntity<DetectionDTO> confirmDetection(@PathVariable Long id) {
        return ResponseEntity.ok(detectionService.confirmDetection(id));
    }

    // ── Helper sauvegarde fichier ────────────────────────────────
    // private String sauvegarderFichier(MultipartFile file) {
    //     if (file == null || file.isEmpty()) return null;
    //     try {
    //         String nom = System.currentTimeMillis() + "_" + file.getOriginalFilename();
    //         Path dest = Paths.get("alertes", nom);
    //         Files.createDirectories(dest.getParent());
    //         file.transferTo(dest.toFile());
    //         return dest.toString().replace("\\", "/");
    //     } catch (IOException e) {
    //         System.err.println("[PREUVE] Erreur sauvegarde : " + e.getMessage());
    //         return null;
    //     }
    // }

    // private String sauvegarderFichier(MultipartFile file) {
    //     if (file == null || file.isEmpty()) return null;
    //     try {
    //         String nom = System.currentTimeMillis() + "_" + file.getOriginalFilename();
    //         // Utiliser storagePath depuis application.properties
    //         Path dest = Paths.get(storagePath, nom).normalize();
    //         Files.createDirectories(dest.getParent());
    //         file.transferTo(dest.toFile());
    //         System.out.println("[FICHIER] ✅ Sauvegardé: " + dest.toAbsolutePath());
    //         // Stocker juste le nom du fichier (pas le chemin complet)
    //         return nom;
    //     } catch (IOException e) {
    //         System.err.println("[FICHIER] ❌ Erreur sauvegarde: " + e.getMessage());
    //         e.printStackTrace();
    //         return null;
    //     }
    // }
    private String sauvegarderFichier(MultipartFile file) {
        if (file == null || file.isEmpty()) return null;
        try {
            String nom = file.getOriginalFilename();
            Path dest = Paths.get(storagePath, nom).normalize();
            Files.createDirectories(dest.getParent());
            file.transferTo(dest.toFile());
            System.out.println("[FICHIER] ✅ Sauvegardé: " + dest.toAbsolutePath());
            return nom;
        } catch (IOException e) {
            System.err.println("[FICHIER] ❌ Erreur sauvegarde: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    //     private String sauvegarderFichier(MultipartFile file) {
    //     if (file == null || file.isEmpty()) return null;
    //     try {
    //         // ✅ Extraire uniquement le nom court — ignore le chemin absolu Windows envoyé par Python
    //         String nomOriginal = Paths.get(file.getOriginalFilename()).getFileName().toString();
    //         String nom = System.currentTimeMillis() + "_" + nomOriginal;

    //         Path dest = Paths.get(storagePath).resolve(nom).normalize();
    //         Files.createDirectories(dest.getParent());
    //         file.transferTo(dest.toFile());
    //         System.out.println("[FICHIER] ✅ Sauvegardé: " + dest.toAbsolutePath());
    //         return nom;  // ex: 1778023950257_alerte_ID1_20260506_003222.jpg
    //     } catch (IOException e) {
    //         System.err.println("[FICHIER] ❌ Erreur: " + e.getMessage());
    //         e.printStackTrace();
    //         return null;
    //     }
    // }
    // private String sauvegarderFichier(MultipartFile file) {
    //     if (file == null || file.isEmpty()) return null;
    //     try {
    //         String nom = System.currentTimeMillis() + "_" + file.getOriginalFilename();
    //         // storagePath = C:/Users/GIGABYTE/.../alertes
    //         Path dest = Paths.get(storagePath).resolve(nom).normalize();
    //         Files.createDirectories(dest.getParent());
    //         file.transferTo(dest.toFile());
    //         System.out.println("[FICHIER] ✅ Sauvegardé: " + dest.toAbsolutePath());
    //         return nom;  // juste le nom, ex: 1778018859806_alerte_ID1_xxx.jpg
    //     } catch (IOException e) {
    //         System.err.println("[FICHIER] ❌ Erreur: " + e.getMessage());
    //         e.printStackTrace();
    //         return null;
    //     }
    // }
}