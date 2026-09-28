package com.ecosurveillance.repository;

import com.ecosurveillance.entity.Preuve;
import com.ecosurveillance.entity.Infraction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PreuveRepository extends JpaRepository<Preuve, Long> {
    List<Preuve> findByInfractionId(Long infractionId);
    // Récupérer toutes les preuves liées à une infraction
    List<Preuve> findByInfraction(Infraction infraction);
}