package com.ecosurveillance.repository;

import com.ecosurveillance.entity.Detection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DetectionRepository extends JpaRepository<Detection, Long> {
    List<Detection> findByConfirmed(boolean confirmed);
    List<Detection> findByUserId(Long userId);
}