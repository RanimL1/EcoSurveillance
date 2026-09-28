package com.ecosurveillance.controller;

import com.ecosurveillance.dto.InfractionDTO;
import com.ecosurveillance.dto.InfractionRequest;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.enums.StatusInfraction;
import com.ecosurveillance.service.InfractionService;
import com.ecosurveillance.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/infractions")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class InfractionController {

    private final InfractionService infractionService;
    private final UserService userService;  // Ajout de UserService

    // Récupérer toutes les infractions
    @GetMapping
    public ResponseEntity<List<InfractionDTO>> getAllInfractions() {
        return ResponseEntity.ok(infractionService.getAllInfractions());
    }

    @GetMapping("/mes-infractions")
    public ResponseEntity<List<InfractionDTO>> getMesInfractions(@RequestParam Long userId) {
        return ResponseEntity.ok(infractionService.getInfractionsByEtudiant(userId));
    }

    // Récupérer les infractions par ID étudiant
    @GetMapping("/etudiant/{etudiantId}")
    public ResponseEntity<List<InfractionDTO>> getInfractionsByEtudiant(@PathVariable Long etudiantId) {
        return ResponseEntity.ok(infractionService.getInfractionsByEtudiant(etudiantId));
    }

    // Récupérer une infraction par ID
    @GetMapping("/{id}")
    public ResponseEntity<InfractionDTO> getInfractionById(@PathVariable Long id) {
        return ResponseEntity.ok(infractionService.getInfractionDTOById(id));
    }

    // Créer une infraction
    @PostMapping
    public ResponseEntity<InfractionDTO> createInfraction(@RequestBody InfractionRequest request) {
        return ResponseEntity.ok(infractionService.createInfraction(request));
    }

    // Mettre à jour le statut
    @PatchMapping("/{id}/status")
    public ResponseEntity<InfractionDTO> updateStatus(
            @PathVariable Long id,
            @RequestParam StatusInfraction status) {
        return ResponseEntity.ok(infractionService.updateStatus(id, status));
    }

    // Supprimer une infraction
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteInfraction(@PathVariable Long id) {
        infractionService.deleteInfraction(id);
        return ResponseEntity.noContent().build();
    }

    // Compter les infractions
    @GetMapping("/count")
    public ResponseEntity<Long> countInfractions() {
        return ResponseEntity.ok(infractionService.countInfractions());
    }

    // Infractions par statut
    @GetMapping("/status/{status}")
    public ResponseEntity<List<InfractionDTO>> getInfractionsByStatus(@PathVariable StatusInfraction status) {
        return ResponseEntity.ok(infractionService.getInfractionsByStatus(status));
    }
    // Ajouter dans InfractionController.java

    // Valider une punition (passe infraction + punition à TERMINEE)
    @PatchMapping("/{id}/valider")
    public ResponseEntity<InfractionDTO> validerPunition(@PathVariable Long id) {
        return ResponseEntity.ok(infractionService.validerPunition(id));
    }
}