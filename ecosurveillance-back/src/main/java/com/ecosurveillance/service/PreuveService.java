package com.ecosurveillance.service;

import com.ecosurveillance.entity.Preuve;
import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.repository.PreuveRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class PreuveService {
    public List<Preuve> findByInfractionId(Long id) {
        return preuveRepository.findByInfractionId(id);
    }
    private final PreuveRepository preuveRepository;

    public PreuveService(PreuveRepository preuveRepository) {
        this.preuveRepository = preuveRepository;
    }

    public List<Preuve> getAllPreuves() {
        return preuveRepository.findAll();
    }

    public Optional<Preuve> getPreuveById(Long id) {
        return preuveRepository.findById(id);
    }

    public Preuve savePreuve(Preuve preuve) {
        return preuveRepository.save(preuve);
    }

    public void deletePreuve(Long id) {
        preuveRepository.deleteById(id);
    }

    public List<Preuve> getPreuvesByInfraction(Infraction infraction) {
        return preuveRepository.findByInfraction(infraction);
    }
}