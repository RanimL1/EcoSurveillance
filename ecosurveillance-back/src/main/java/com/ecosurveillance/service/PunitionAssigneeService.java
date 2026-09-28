package com.ecosurveillance.service;

import com.ecosurveillance.entity.PunitionAssignee;
import com.ecosurveillance.repository.PunitionAssigneeRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class PunitionAssigneeService {

    private final PunitionAssigneeRepository repository;

    public PunitionAssigneeService(PunitionAssigneeRepository repository) {
        this.repository = repository;
    }

    public List<PunitionAssignee> getAllPunitionAssignee() {
        return repository.findAll();
    }

    public Optional<PunitionAssignee> getPunitionAssigneeById(Long id) {
        return repository.findById(id);
    }

    public PunitionAssignee savePunitionAssignee(PunitionAssignee punitionAssignee) {
        return repository.save(punitionAssignee);
    }

    public void deletePunitionAssignee(Long id) {
        repository.deleteById(id);
    }

    public List<PunitionAssignee> getByInfractionId(Long infractionId) {
        return repository.findByInfractionId(infractionId);
    }
}