package com.ecosurveillance.service;

import com.ecosurveillance.dto.InfractionDTO;
import com.ecosurveillance.dto.InfractionRequest;
import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.entity.PunitionAssignee;
import com.ecosurveillance.entity.PunitionEcologique;
import com.ecosurveillance.entity.Preuve;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.enums.StatusInfraction;
import com.ecosurveillance.repository.InfractionRepository;
import com.ecosurveillance.repository.PunitionAssigneeRepository;
import com.ecosurveillance.repository.PunitionEcologiqueRepository;
import com.ecosurveillance.repository.PreuveRepository;
import com.ecosurveillance.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class InfractionService {

    private final InfractionRepository infractionRepository;
    private final UserRepository userRepository;
    private final PreuveRepository preuveRepository;
    private final PunitionAssigneeRepository punitionAssigneeRepository;
    private final PunitionEcologiqueRepository punitionEcologiqueRepository;

    // =========================
    // CREATE
    // =========================
    @Transactional
    public InfractionDTO createInfraction(InfractionRequest request) {

        User etudiant = userRepository.findById(request.getEtudiantId())
                .orElseThrow(() -> new RuntimeException("Etudiant non trouvé"));

        Infraction infraction = Infraction.builder()
                .etudiant(etudiant)
                .status(StatusInfraction.EN_ATTENTE)
                .build();

        Infraction saved = infractionRepository.save(infraction);

        // Ajouter les preuves
        if (request.getPreuves() != null && !request.getPreuves().isEmpty()) {
            for (Preuve preuve : request.getPreuves()) {
                preuve.setInfraction(saved);
                preuveRepository.save(preuve);
            }
        }

        // Assigner une punition écologique aléatoire
        PunitionAssignee punition = assignRandomPunition(saved);
        punitionAssigneeRepository.save(punition);

        return mapToDTO(saved);
    }

    // =========================
    // READ
    // =========================
    public List<InfractionDTO> getAllInfractions() {
        return infractionRepository.findAll()
                .stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }

    public Optional<Infraction> getInfractionById(Long id) {
        return infractionRepository.findById(id);
    }

    public List<InfractionDTO> getInfractionsByEtudiant(Long etudiantId) {

        User etudiant = userRepository.findById(etudiantId)
                .orElseThrow(() -> new RuntimeException("Etudiant non trouvé"));

        return infractionRepository.findByEtudiant(etudiant)
                .stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }
    // Count total
    public long countInfractions() {
        return infractionRepository.count();
    }

    // Par status
    public List<InfractionDTO> getInfractionsByStatus(StatusInfraction status) {
        return infractionRepository.findByStatus(status)
                .stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }

    // Get by ID → retourne DTO (pas Optional)
    public InfractionDTO getInfractionDTOById(Long id) {
        Infraction infraction = infractionRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Infraction non trouvée"));
        return mapToDTO(infraction);
    }

    // =========================
    // UPDATE
    // =========================
    @Transactional
    public InfractionDTO updateStatus(Long infractionId, StatusInfraction status) {

        Infraction infraction = infractionRepository.findById(infractionId)
                .orElseThrow(() -> new RuntimeException("Infraction non trouvée"));

        infraction.setStatus(status);

        return mapToDTO(infractionRepository.save(infraction));
    }

    // =========================
    // DELETE
    // =========================
    public void deleteInfraction(Long id) {
        infractionRepository.deleteById(id);
    }

    // =========================
    // LOGIQUE MÉTIER
    // =========================
    private PunitionAssignee assignRandomPunition(Infraction infraction) {

        List<PunitionEcologique> punitions = punitionEcologiqueRepository.findAll();

        if (punitions.isEmpty()) {
            throw new RuntimeException("Aucune punition écologique disponible");
        }

        // Choisir une punition aléatoire
        PunitionEcologique randomPunition =
                punitions.get((int) (Math.random() * punitions.size()));

        // Créer une nouvelle assignation
        PunitionAssignee assignee = new PunitionAssignee();
        assignee.setInfraction(infraction);
        assignee.setPunition(randomPunition);
        assignee.setStatut("EN_ATTENTE");

        return assignee;
    }


    // =========================
    // MAPPING DTO
    // =========================
    // private InfractionDTO mapToDTO(Infraction infraction) {

    //     InfractionDTO dto = new InfractionDTO();

    //     dto.setId(infraction.getId());
    //     dto.setEtudiantNom(infraction.getEtudiant().getNom());
    //     dto.setEtudiantEmail(infraction.getEtudiant().getEmail());
    //     dto.setDate(infraction.getInfractionDate());
    //     dto.setStatus(infraction.getStatus());

    //     // preuves
    //     List<Preuve> preuves = preuveRepository.findByInfraction(infraction);
    //     dto.setPreuves(preuves);

    //     // punition assignée
    //     PunitionAssignee punition = punitionAssigneeRepository
    //             .findByInfraction(infraction)
    //             .orElse(null);

    //     if (punition != null) {
    //         dto.setPunitionDescription(punition.getPunition().getDescription());
    //         dto.setPunitionStatut(punition.getStatut());
    //     }

    //     return dto;

    // }
    // Remplacer la méthode validerPunition dans InfractionService.java

    @Transactional
    public InfractionDTO validerPunition(Long infractionId) {

        Infraction infraction = infractionRepository.findById(infractionId)
                .orElseThrow(() -> new RuntimeException("Infraction non trouvée"));

        // 1. Passer l'infraction à TERMINEE
        infraction.setStatus(StatusInfraction.TERMINEE);
        infractionRepository.save(infraction);

        // 2. Passer la punition à TERMINEE si elle existe
        // CORRECTION : orElse(null) au lieu de orElseThrow
        PunitionAssignee punition = punitionAssigneeRepository
                .findByInfraction(infraction)
                .orElse(null);

        if (punition != null) {
            // Punition existante → la terminer
            punition.setStatut("TERMINEE");
            punitionAssigneeRepository.save(punition);
        } else {
            // Pas de punition assignée → en créer une automatiquement
            List<PunitionEcologique> punitions = punitionEcologiqueRepository.findAll();
            if (!punitions.isEmpty()) {
                PunitionEcologique randomPunition =
                        punitions.get((int) (Math.random() * punitions.size()));
                PunitionAssignee newPunition = new PunitionAssignee();
                newPunition.setInfraction(infraction);
                newPunition.setPunition(randomPunition);
                newPunition.setStatut("TERMINEE");
                punitionAssigneeRepository.save(newPunition);
            }
        }

        return mapToDTO(infraction);
    }

    private InfractionDTO mapToDTO(Infraction infraction) {
 
        InfractionDTO dto = new InfractionDTO();
 
        dto.setId(infraction.getId());
        dto.setNom((infraction.getEtudiant() != null ? infraction.getEtudiant().getNom() : "Inconnu"));
        dto.setPrenom((infraction.getEtudiant() != null ? infraction.getEtudiant().getPrenom() : "Inconnu"));
        dto.setEtudiantEmail(infraction.getEtudiant() != null ? infraction.getEtudiant().getEmail() : "");
        dto.setDate(infraction.getInfractionDate());
        dto.setStatus(infraction.getStatus());
 
        // ← REMPLACÉ : extraire juste les URLs, pas les entités Preuve
        List<Preuve> preuves = preuveRepository.findByInfraction(infraction);
        dto.setImageUrls(preuves.stream()
                .map(Preuve::getImageUrl)
                .filter(url -> url != null && !url.isEmpty())
                .collect(Collectors.toList()));
        dto.setVideoUrls(preuves.stream()
                .map(Preuve::getVideoUrl)
                .filter(url -> url != null && !url.isEmpty())
                .collect(Collectors.toList()));
 
        // punition assignée
        PunitionAssignee punition = punitionAssigneeRepository
                .findByInfraction(infraction)
                .orElse(null);
 
        if (punition != null) {
            dto.setPunitionDescription(punition.getPunition().getDescription());
            dto.setPunitionStatut(punition.getStatut());
        }
 
        return dto;
    }
    // Ajouter cette méthode dans InfractionService.java
    public List<InfractionDTO> getInfractionsByCurrentUser(User currentUser) {
        return infractionRepository.findByEtudiant(currentUser)
                .stream()
                .map(this::mapToDTO)
                .collect(Collectors.toList());
    }
}