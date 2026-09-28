package com.ecosurveillance.dto;

import lombok.Data;

@Data
public class FaceVectorDTO {
    private Long userId;
    private String vector;
}
