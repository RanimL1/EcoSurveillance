package com.ecosurveillance.repository;

import com.ecosurveillance.entity.PunitionAssignee;
import com.ecosurveillance.entity.Infraction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface PunitionAssigneeRepository extends JpaRepository<PunitionAssignee, Long> {

    List<PunitionAssignee> findByInfractionId(Long infractionId);
    long countByStatut(String statut);

    long countByInfraction_InfractionDateAfter(LocalDateTime date);
    Optional<PunitionAssignee> findByInfraction(Infraction infraction);
}