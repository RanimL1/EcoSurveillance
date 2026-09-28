package com.ecosurveillance.repository;

import com.ecosurveillance.entity.Camera;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CameraRepository extends JpaRepository<Camera, Long> {
    List<Camera> findByActive(Boolean active);
    Long countByActive(Boolean active);
}