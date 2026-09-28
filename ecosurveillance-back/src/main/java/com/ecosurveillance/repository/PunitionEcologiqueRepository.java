package com.ecosurveillance.repository;

import com.ecosurveillance.entity.PunitionEcologique;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PunitionEcologiqueRepository extends JpaRepository<PunitionEcologique, Long> {
}