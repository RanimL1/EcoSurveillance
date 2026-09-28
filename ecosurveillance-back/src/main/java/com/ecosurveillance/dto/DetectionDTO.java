package com.ecosurveillance.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class DetectionDTO {
    private Long id;
    private String type;
    private LocalDateTime detectedAt;
    private boolean confirmed;
    private Long userId;
}
