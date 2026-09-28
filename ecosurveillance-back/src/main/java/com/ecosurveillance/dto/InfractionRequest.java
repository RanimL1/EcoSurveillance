package com.ecosurveillance.dto;

import com.ecosurveillance.entity.Preuve;
import lombok.Data;

import java.util.List;

@Data
public class InfractionRequest {

    private Long etudiantId;

    private List<Preuve> preuves;
}