package com.ecosurveillance.service;

import com.ecosurveillance.dto.FaceVectorDTO;
import com.ecosurveillance.entity.FaceVector;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.repository.FaceVectorRepository;
import com.ecosurveillance.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class FaceVectorService {

    private final FaceVectorRepository faceVectorRepository;
    private final UserRepository userRepository;

    public void saveVector(FaceVectorDTO dto) {
        User user = userRepository.findById(dto.getUserId())
                .orElseThrow();

        FaceVector vector = FaceVector.builder()
                .vector(dto.getVector())
                .user(user)
                .build();

        faceVectorRepository.save(vector);
    }
}
