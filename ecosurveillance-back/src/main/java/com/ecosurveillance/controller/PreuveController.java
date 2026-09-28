package com.ecosurveillance.controller;

import com.ecosurveillance.entity.Detection;
import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.repository.InfractionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/api/preuves")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class PreuveController {

    private final InfractionRepository infractionRepository;
    
    @Value("${preuves.storage.path}")
    private String storagePath;

    // @GetMapping("/infraction/{infractionId}")
    // public ResponseEntity<List<Map<String, String>>> getPreuvesByInfraction(@PathVariable Long infractionId) {
    //     Optional<Infraction> infractionOpt = infractionRepository.findById(infractionId);
        
    //     if (infractionOpt.isEmpty()) {
    //         return ResponseEntity.ok(new ArrayList<>());
    //     }
        
    //     Infraction infraction = infractionOpt.get();
    //     List<Map<String, String>> result = new ArrayList<>();
        
    //     String preuveUrl = infraction.getPreuveUrl();
    //     if (preuveUrl != null && !preuveUrl.isEmpty()) {
    //         Map<String, String> preuveMap = new HashMap<>();
    //         preuveMap.put("id", String.valueOf(infraction.getId()));
    //         preuveMap.put("type", "IMAGE");
    //         preuveMap.put("photoUrl", "/api/preuves/media/" + preuveUrl);
    //         preuveMap.put("videoUrl", "");
    //         result.add(preuveMap);
    //     }
        
    //     return ResponseEntity.ok(result);
    // }

    // @GetMapping("/infraction/{infractionId}")
    // public ResponseEntity<List<Map<String, String>>> getPreuvesByInfraction(
    //         @PathVariable Long infractionId) {

    //     Optional<Infraction> opt = infractionRepository.findById(infractionId);
    //     if (opt.isEmpty()) return ResponseEntity.ok(new ArrayList<>());

    //     Infraction infraction = opt.get();
    //     List<Map<String, String>> result = new ArrayList<>();

    //     String preuveUrl = infraction.getPreuveUrl(); // ex: alertes/alerte_ID1_xxx.jpg
    //     if (preuveUrl != null && !preuveUrl.isEmpty()) {
    //         Map<String, String> map = new HashMap<>();
    //         map.put("id", String.valueOf(infraction.getId()));
    //         map.put("photoUrl", "/api/preuves/media/" + preuveUrl);

    //         // Déduire le chemin vidéo depuis le chemin image
    //         // alertes/alerte_ID1_20260505_143712.jpg
    //         // → alertes/clip_ID1_20260505_143712.mp4  (même timestamp)
    //         String videoUrl = preuveUrl
    //                 .replace("alerte_ID", "clip_ID")
    //                 .replaceAll("\\.jpg$", ".mp4");

    //         // Vérifier que le fichier vidéo existe physiquement
    //         Path videoPath = Paths.get(storagePath, videoUrl);
    //         if (Files.exists(videoPath)) {
    //             map.put("videoUrl", "/api/preuves/media/" + videoUrl);
    //         } else {
    //             map.put("videoUrl", "");
    //         }

    //         result.add(map);
    //     }

    //     return ResponseEntity.ok(result);
    // }

    @GetMapping("/infraction/{infractionId}")
    public ResponseEntity<List<Map<String, String>>> getPreuvesByInfraction(
            @PathVariable Long infractionId) {

        Optional<Infraction> opt = infractionRepository.findById(infractionId);
        if (opt.isEmpty()) return ResponseEntity.ok(new ArrayList<>());

        Infraction infraction = opt.get();
        List<Map<String, String>> result = new ArrayList<>();
        Map<String, String> map = new HashMap<>();
        map.put("id", String.valueOf(infraction.getId()));

        Detection detection = infraction.getDetection();
        if (detection != null) {
            map.put("photoUrl", detection.getCapturePath() != null
                    ? "/api/preuves/media/" + detection.getCapturePath() : "");
            map.put("videoUrl", detection.getVideoPath() != null
                    ? "/api/preuves/media/" + detection.getVideoPath() : "");
        } else {
            // Fallback ancien pipeline
            map.put("photoUrl", infraction.getPreuveUrl() != null
                    ? "/api/preuves/media/" + infraction.getPreuveUrl() : "");
            map.put("videoUrl", "");
        }

        if (!map.get("photoUrl").isEmpty() || !map.get("videoUrl").isEmpty()) {
            result.add(map);
        }

        return ResponseEntity.ok(result);
    }

    // @GetMapping("/media/**")
    // public ResponseEntity<Resource> servirMedia(HttpServletRequest request) throws IOException {
    //     // Exemple: "alertes/alerte_ID1_20260324_163200.jpg"
    //     String cheminRelatif = request.getRequestURI().replaceFirst("/api/preuves/media/", "");
        
    //     // Combine: C:/Users/GIGABYTE/Desktop/liaison/detection_main/detection_aoi + alertes/alerte_ID1_20260324_163200.jpg
    //     Path filePath = Paths.get(storagePath, cheminRelatif).normalize();
        
    //     System.out.println("🔍 Recherche fichier: " + filePath.toString()); // Pour voir le chemin dans la console
        
    //     Resource resource = new UrlResource(filePath.toUri());

    //     if (!resource.exists()) {
    //         System.out.println("❌ Fichier non trouvé: " + filePath.toString());
    //         return ResponseEntity.notFound().build();
    //     }

    //     String contentType = Files.probeContentType(filePath);
    //     if (contentType == null) contentType = "image/jpeg";

    //     return ResponseEntity.ok()
    //             .contentType(MediaType.parseMediaType(contentType))
    //             .header("Content-Disposition", "inline")
    //             .body(resource);
    // }
//     @GetMapping("/media/**")
//     public ResponseEntity<Resource> servirMedia(HttpServletRequest request) throws IOException {
//         String cheminRelatif = request.getRequestURI().replaceFirst("/api/preuves/media/", "");
//         Path filePath = Paths.get(storagePath, cheminRelatif).normalize();

//         System.out.println("🔍 Recherche fichier: " + filePath.toString());

//         Resource resource = new UrlResource(filePath.toUri());

//         if (!resource.exists()) {
//             System.out.println("❌ Fichier non trouvé: " + filePath.toString());
//             return ResponseEntity.notFound().build();
//         }

//         String contentType = Files.probeContentType(filePath);
//         if (contentType == null) {
//             contentType = filePath.toString().endsWith(".mp4") ? "video/mp4" : "image/jpeg";
//         }

//         return ResponseEntity.ok()
//                 .contentType(MediaType.parseMediaType(contentType))
//                 .header("Content-Disposition", "inline")
//                 .header("Accept-Ranges", "bytes")           // ← indique au navigateur que le range est supporté
//                 .header("Cache-Control", "no-cache")
//                 .contentLength(Files.size(filePath))        // ← taille obligatoire pour le streaming
//                 .body(resource);
//     }
// }

    @GetMapping("/media/**")
        public ResponseEntity<Resource> servirMedia(HttpServletRequest request) throws IOException {
            String cheminRelatif = request.getRequestURI().replaceFirst("/api/preuves/media/", "");
            Path filePath = Paths.get(storagePath, cheminRelatif).normalize();

            System.out.println("🔍 Recherche fichier: " + filePath.toString());

            Resource resource = new UrlResource(filePath.toUri());

            if (!resource.exists()) {
                System.out.println("❌ Fichier non trouvé: " + filePath.toString());
                return ResponseEntity.notFound().build();
            }

            String contentType = Files.probeContentType(filePath);
            if (contentType == null) {
                contentType = filePath.toString().endsWith(".mp4") ? "video/mp4" : "image/jpeg";
            }

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header("Content-Disposition", "inline")
                    .header("Accept-Ranges", "bytes")
                    .header("Cache-Control", "no-cache")
                    .contentLength(Files.size(filePath))
                    .body(resource);
        }
}