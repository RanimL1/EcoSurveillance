package com.ecosurveillance.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class EtudiantListDTO {
    private String nom;
    private String prenom;
    private String email;
    private Long infractions;
    private String dernierePunition;
    // AJOUT : date de la dernière infraction
    private LocalDateTime derniereInfractionDate;
}