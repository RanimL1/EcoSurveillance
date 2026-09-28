package com.ecosurveillance.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToOne;
import lombok.Getter;
import lombok.Setter;
import jakarta.persistence.Id;

@Entity
@Getter
@Setter
public class PunitionAssignee {

    @Id
    @GeneratedValue
    private Long id;

    private String statut;

    @ManyToOne
    private PunitionEcologique punition;

    @OneToOne
    private Infraction infraction;
}