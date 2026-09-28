package com.ecosurveillance.dto;

import com.ecosurveillance.entity.Preuve;
import com.ecosurveillance.enums.StatusInfraction;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class InfractionDTO {

    private Long id;

    private String  nom;
    private String prenom;

    private String etudiantEmail;

    private LocalDateTime date;
    private StatusInfraction status;

    private List<String> imageUrls;
    private List<String> videoUrls;

    private String punitionDescription;
    private String punitionStatut;
}