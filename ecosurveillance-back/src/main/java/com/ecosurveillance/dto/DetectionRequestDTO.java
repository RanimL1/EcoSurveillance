package com.ecosurveillance.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DetectionRequestDTO {
    private String type;
    private String trackId;
    private String bboxCoordinates;
    private String userId;
    private MultipartFile photo;
    private MultipartFile video;
}