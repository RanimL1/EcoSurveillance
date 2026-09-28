package com.ecosurveillance.service;

import com.ecosurveillance.entity.PunitionEcologique;
import com.ecosurveillance.repository.PunitionEcologiqueRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class PunitionEcologiqueService {

    private final PunitionEcologiqueRepository repository;

    public PunitionEcologiqueService(PunitionEcologiqueRepository repository) {
        this.repository = repository;
    }

    public List<PunitionEcologique> getAllPunition() {
        return repository.findAll();
    }

    public Optional<PunitionEcologique> getPunitionById(Long id) {
        return repository.findById(id);
    }

    public PunitionEcologique savePunition(PunitionEcologique punition) {
        return repository.save(punition);
    }

    public void deletePunition(Long id) {
        repository.deleteById(id);
    }
}