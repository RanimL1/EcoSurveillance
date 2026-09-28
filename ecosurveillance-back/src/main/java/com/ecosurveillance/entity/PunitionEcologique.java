package com.ecosurveillance.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import lombok.Getter;
import lombok.Setter;
import jakarta.persistence.Id;

@Entity
@Getter
@Setter
public class PunitionEcologique {

    @Id
    @GeneratedValue
    private Long id;

    private String description;
}
