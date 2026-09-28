package com.ecosurveillance.dto;

import lombok.Data;

@Data
public class EtudiantStatsDTO {

    private Long totalInfractions;
    private Long punitionsTerminees;
    private Long punitionsNonTerminees;
}