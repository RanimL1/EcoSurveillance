package com.ecosurveillance.controller;

import com.ecosurveillance.entity.PunitionEcologique;
import com.ecosurveillance.service.PunitionEcologiqueService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/punitions")
public class PunitionEcologiqueController {

    private final PunitionEcologiqueService service;

    public PunitionEcologiqueController(PunitionEcologiqueService service) {
        this.service = service;
    }

    @GetMapping
    public List<PunitionEcologique> getAll() {
        return service.getAllPunition();
    }

    @GetMapping("/{id}")
    public PunitionEcologique getById(@PathVariable Long id) {
        return service.getPunitionById(id).orElse(null);
    }

    @PostMapping
    public PunitionEcologique create(@RequestBody PunitionEcologique punition) {
        return service.savePunition(punition);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        service.deletePunition(id);
    }
}