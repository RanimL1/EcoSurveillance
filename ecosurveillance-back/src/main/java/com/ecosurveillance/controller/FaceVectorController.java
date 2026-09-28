package com.ecosurveillance.controller;

import com.ecosurveillance.dto.FaceVectorDTO;
import com.ecosurveillance.service.FaceVectorService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/student/vector")
@RequiredArgsConstructor
public class FaceVectorController {

    private final FaceVectorService faceVectorService;

    @PostMapping
    public void save(@RequestBody FaceVectorDTO dto) {
        faceVectorService.saveVector(dto);
    }
}
