package com.ecosurveillance.repository;

import com.ecosurveillance.entity.FaceVector;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface FaceVectorRepository extends JpaRepository<FaceVector, Long> {
    Optional<FaceVector> findByUserId(Long userId);
}
