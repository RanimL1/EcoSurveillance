package com.ecosurveillance.controller;

import com.ecosurveillance.entity.PunitionAssignee;
import com.ecosurveillance.service.PunitionAssigneeService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/punition-assignee")
public class PunitionAssigneeController {

    private final PunitionAssigneeService service;

    public PunitionAssigneeController(PunitionAssigneeService service) {
        this.service = service;
    }

    @GetMapping
    public List<PunitionAssignee> getAll() {
        return service.getAllPunitionAssignee();
    }

    @GetMapping("/{id}")
    public PunitionAssignee getById(@PathVariable Long id) {
        return service.getPunitionAssigneeById(id).orElse(null);
    }

    @GetMapping("/infraction/{infractionId}")
    public List<PunitionAssignee> getByInfraction(@PathVariable Long infractionId) {
        return service.getByInfractionId(infractionId);
    }

    @PostMapping
    public PunitionAssignee create(@RequestBody PunitionAssignee punitionAssignee) {
        return service.savePunitionAssignee(punitionAssignee);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        service.deletePunitionAssignee(id);
    }
}