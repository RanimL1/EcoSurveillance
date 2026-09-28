package com.ecosurveillance.dto;

import lombok.Data;

@Data
public class DashboardStatsDTO {

    private Long totalInfractions;
    private Long infractionsAujourdhui;

    private Long totalEtudiants;
    private Long totalPunitions;

    private Long punitionsAujourdhui;
    private Long punitionsTerminees;

    private Long camerasActives;
}