// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.DetectionDTO;
// import com.ecosurveillance.entity.Detection;
// import com.ecosurveillance.repository.DetectionRepository;
// import com.ecosurveillance.repository.UserRepository;
// import lombok.RequiredArgsConstructor;
// import org.springframework.stereotype.Service;

// import java.time.LocalDateTime;
// import java.util.List;
// import java.util.stream.Collectors;

// @Service
// @RequiredArgsConstructor
// public class DetectionService {

//     private final DetectionRepository detectionRepository;
//     private final UserRepository userRepository;

//     public Detection createDetection(DetectionDTO dto) {
//         Detection detection = Detection.builder()
//                 .type(dto.getType())
//                 .detectedAt(LocalDateTime.now())
//                 .confirmed(dto.isConfirmed())
//                 .build();

//         if (dto.getUserId() != null) {
//             userRepository.findById(dto.getUserId())
//                     .ifPresent(detection::setUser);
//         }

//         return detectionRepository.save(detection);
//     }

//     public List<Detection> getAllDetections() {
//         return detectionRepository.findAll();
//     }

//     public Detection confirmDetection(Long id) {
//         Detection detection = detectionRepository.findById(id)
//                 .orElseThrow(() -> new RuntimeException("Détection non trouvée"));
//         detection.setConfirmed(true);
//         return detectionRepository.save(detection);
//     }
// }

// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.DetectionDTO;
// import com.ecosurveillance.dto.DetectionRequestDTO;
// import com.ecosurveillance.entity.Detection;
// import com.ecosurveillance.entity.Infraction;
// import com.ecosurveillance.entity.User;
// import com.ecosurveillance.enums.StatusInfraction;
// import com.ecosurveillance.repository.DetectionRepository;
// import com.ecosurveillance.repository.InfractionRepository;
// import com.ecosurveillance.repository.UserRepository;
// import lombok.RequiredArgsConstructor;
// import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Transactional;

// import java.time.LocalDateTime;
// import java.util.List;

// @Service
// @RequiredArgsConstructor
// public class DetectionService {
    
//     private final DetectionRepository detectionRepository;
//     private final UserRepository userRepository;
//     private final InfractionRepository infractionRepository;
    
//     // Méthode existante pour le DTO original
//     @Transactional
//     public Detection createDetection(DetectionDTO dto) {
//         Detection detection = Detection.builder()
//             .type(dto.getType())
//             .detectedAt(dto.getDetectedAt() != null ? dto.getDetectedAt() : LocalDateTime.now())
//             .confirmed(dto.isConfirmed())
//             .build();
        
//         if (dto.getUserId() != null) {
//             User user = userRepository.findById(dto.getUserId()).orElse(null);
//             detection.setUser(user);
//         }
        
//         return detectionRepository.save(detection);
//     }
    
//     // Nouvelle méthode pour Python
//     @Transactional
//     public Detection createDetectionFromPython(DetectionRequestDTO dto) {
//         Detection detection = Detection.builder()
//             .type(dto.getType())
//             .detectedAt(LocalDateTime.now())
//             .confirmed(false)
//             .trackId(dto.getTrackId())
//             .capturePath(dto.getCapturePath())
//             .bboxCoordinates(dto.getBboxCoordinates())
//             .build();
        
//         if (dto.getUserId() != null) {
//             User user = userRepository.findById(dto.getUserId()).orElse(null);
//             detection.setUser(user);
            
//             // Créer une infraction automatiquement
//             if (user != null) {
//                 Infraction infraction = Infraction.builder()
//                     .etudiant(user)
//                     .description("Jet de déchet détecté - Track ID: " + dto.getTrackId())
//                     .infractionDate(LocalDateTime.now())
//                     .status(StatusInfraction.EN_ATTENTE)
//                     .preuveUrl(dto.getCapturePath())
//                     .build();
                
//                 infraction = infractionRepository.save(infraction);
//                 detection.setInfraction(infraction);
//             }
//         }
        
//         return detectionRepository.save(detection);
//     }
    
//     // Récupérer toutes les détections
//     public List<Detection> getAllDetections() {
//         return detectionRepository.findAll();
//     }
    
//     // Confirmer une détection
//     @Transactional
//     public Detection confirmDetection(Long id) {
//         Detection detection = detectionRepository.findById(id)
//             .orElseThrow(() -> new RuntimeException("Détection non trouvée avec l'id: " + id));
        
//         detection.setConfirmed(true);
//         return detectionRepository.save(detection);
//     }
// }

// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.DetectionRequestDTO;
// import com.ecosurveillance.entity.*;
// import com.ecosurveillance.enums.StatusInfraction;
// import com.ecosurveillance.repository.*;
// import lombok.RequiredArgsConstructor;
// import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Transactional;
// import org.springframework.web.multipart.MultipartFile;
// import java.io.IOException;
// import java.nio.file.Files;
// import java.nio.file.Path;
// import java.nio.file.Paths;
// import java.time.LocalDateTime;
// import java.util.UUID;
// import java.util.List;
// import com.ecosurveillance.dto.InfractionDTO;  // Ajouter cette ligne
// @Service
// @RequiredArgsConstructor
// public class DetectionService {

//     private final InfractionRepository infractionRepository;
//     private final PreuveRepository preuveRepository;
//     private final UserRepository userRepository;
//     private final PunitionEcologiqueRepository punitionEcologiqueRepository;
//     private final PunitionAssigneeRepository punitionAssigneeRepository;
    
//     private final String UPLOAD_DIR = "uploads/";

//     @Transactional
//     public InfractionDTO createDetectionFromPython(DetectionRequestDTO request) {
//         try {
//             // Créer le dossier d'upload s'il n'existe pas
//             Path uploadPath = Paths.get(UPLOAD_DIR);
//             if (!Files.exists(uploadPath)) {
//                 Files.createDirectories(uploadPath);
//             }
            
//             // Récupérer l'étudiant si userId est fourni
//             User etudiant = null;
//             if (request.getUserId() != null && !request.getUserId().isEmpty()) {
//                 Long userId = Long.parseLong(request.getUserId());
//                 etudiant = userRepository.findById(userId).orElse(null);
//             }
            
//             // Créer l'infraction
//             Infraction infraction = Infraction.builder()
//                     .etudiant(etudiant)
//                     .status(StatusInfraction.EN_ATTENTE)
//                     .infractionDate(LocalDateTime.now())
//                     .build();
            
//             Infraction savedInfraction = infractionRepository.save(infraction);
            
//             // Sauvegarder les preuves
//             if (request.getPhoto() != null && !request.getPhoto().isEmpty()) {
//                 String photoFilename = saveFile(request.getPhoto(), "photo_" + savedInfraction.getId());
//                 Preuve preuve = new Preuve();
//                 preuve.setInfraction(savedInfraction);
//                 preuve.setImageUrl(photoFilename);
//                 preuveRepository.save(preuve);
//             }
            
//             if (request.getVideo() != null && !request.getVideo().isEmpty()) {
//                 String videoFilename = saveFile(request.getVideo(), "video_" + savedInfraction.getId());
//                 Preuve preuve = new Preuve();
//                 preuve.setInfraction(savedInfraction);
//                 preuve.setVideoUrl(videoFilename);
//                 preuveRepository.save(preuve);
//             }
            
//             // Assigner une punition aléatoire
//             assignRandomPunition(savedInfraction);
            
//             // Retourner le DTO
//             return mapToDTO(savedInfraction);
            
//         } catch (IOException e) {
//             throw new RuntimeException("Erreur lors de la sauvegarde des fichiers: " + e.getMessage());
//         }
//     }
    
//     private String saveFile(MultipartFile file, String prefix) throws IOException {
//         String originalFilename = file.getOriginalFilename();
//         String extension = originalFilename != null && originalFilename.contains(".") 
//                 ? originalFilename.substring(originalFilename.lastIndexOf(".")) 
//                 : "";
        
//         String filename = prefix + "_" + UUID.randomUUID().toString() + extension;
//         Path filePath = Paths.get(UPLOAD_DIR, filename);
//         Files.write(filePath, file.getBytes());
        
//         return filename;
//     }
    
//     private void assignRandomPunition(Infraction infraction) {
//         List<PunitionEcologique> punitions = punitionEcologiqueRepository.findAll();
        
//         if (!punitions.isEmpty()) {
//             PunitionEcologique randomPunition = punitions.get((int) (Math.random() * punitions.size()));
            
//             PunitionAssignee assignee = new PunitionAssignee();
//             assignee.setInfraction(infraction);
//             assignee.setPunition(randomPunition);
//             assignee.setStatut("EN_ATTENTE");
            
//             punitionAssigneeRepository.save(assignee);
//         }
//     }
    
//     private InfractionDTO mapToDTO(Infraction infraction) {
//         InfractionDTO dto = new InfractionDTO();
//         dto.setId(infraction.getId());
//         if (infraction.getEtudiant() != null) {
//             dto.setEtudiantNom(infraction.getEtudiant().getNom());
//             dto.setEtudiantEmail(infraction.getEtudiant().getEmail());
//         }
//         dto.setDate(infraction.getInfractionDate());
//         dto.setStatus(infraction.getStatus());
        
//         // Récupérer les preuves
//         List<Preuve> preuves = preuveRepository.findByInfraction(infraction);
//         dto.setPreuves(preuves);
        
//         return dto;
//     }
// }

package com.ecosurveillance.service;

import com.ecosurveillance.dto.DetectionDTO;
import com.ecosurveillance.entity.Detection;
import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.enums.StatusInfraction;
import com.ecosurveillance.repository.DetectionRepository;
import com.ecosurveillance.repository.InfractionRepository;
import com.ecosurveillance.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class DetectionService {

    private final DetectionRepository detectionRepository;
    private final InfractionRepository infractionRepository;
    private final UserRepository userRepository;


    public Detection createDetectionFromPython(String type, String trackId, String userId, String bboxCoordinates) {
        Detection detection = new Detection();
        detection.setType(type);
        if (trackId != null && !trackId.isEmpty()) {
            detection.setTrackId(Integer.parseInt(trackId));
        }
        detection.setBboxCoordinates(bboxCoordinates);
        detection.setDetectedAt(LocalDateTime.now());
        detection.setConfirmed(false);

        // Infraction créée UNIQUEMENT si un étudiant est identifié
        if (userId != null && !userId.isEmpty()) {
            userRepository.findById(Long.parseLong(userId)).ifPresent(user -> {
                Infraction infraction = new Infraction();
                infraction.setEtudiant(user);
                infraction.setDescription("Jet de déchet détecté - Track ID: " + trackId);
                infraction.setStatus(StatusInfraction.EN_ATTENTE);
                infraction.setInfractionDate(LocalDateTime.now());
                infraction.setCreatedAt(LocalDateTime.now());
                Infraction saved = infractionRepository.save(infraction);
                detection.setInfraction(saved);
            });
        }
        // Si userId=null → détection sauvegardée sans infraction (auteur inconnu)

        return detectionRepository.save(detection);
    }

    // Méthode avec DTO
    public DetectionDTO createDetection(DetectionDTO dto) {
        Detection detection = new Detection();
        detection.setType(dto.getType());
        detection.setDetectedAt(LocalDateTime.now());
        detection.setConfirmed(false);
        
        if (dto.getUserId() != null) {
            userRepository.findById(dto.getUserId()).ifPresent(user -> {
                Infraction infraction = new Infraction();
                infraction.setEtudiant(user);
                infraction.setStatus(StatusInfraction.EN_ATTENTE);
                infraction.setInfractionDate(LocalDateTime.now());
                Infraction saved = infractionRepository.save(infraction);
                detection.setInfraction(saved);
            });
        }
        
        Detection saved = detectionRepository.save(detection);
        return mapToDTO(saved);
    }

    // Récupérer toutes les détections
    public List<DetectionDTO> getAllDetections() {
        return detectionRepository.findAll().stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }

    // Confirmer une détection
    public DetectionDTO confirmDetection(Long id) {
        Detection detection = detectionRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Détection non trouvée"));
        detection.setConfirmed(true);
        Detection saved = detectionRepository.save(detection);
        return mapToDTO(saved);
    }
    
    // Mapping helper
    private DetectionDTO mapToDTO(Detection detection) {
        DetectionDTO dto = new DetectionDTO();
        dto.setId(detection.getId());
        dto.setType(detection.getType());
        dto.setDetectedAt(detection.getDetectedAt());
        dto.setConfirmed(detection.isConfirmed());
        if (detection.getInfraction() != null && detection.getInfraction().getEtudiant() != null) {
            dto.setUserId(detection.getInfraction().getEtudiant().getId());
        }
        return dto;
    }
}