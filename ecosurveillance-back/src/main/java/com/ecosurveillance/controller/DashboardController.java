package com.ecosurveillance.controller;

import com.ecosurveillance.dto.DashboardStatsDTO;
import com.ecosurveillance.dto.EtudiantListDTO;
import com.ecosurveillance.service.DashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class DashboardController {

    private final DashboardService dashboardService;

    @GetMapping("/admin/stats")
    public ResponseEntity<DashboardStatsDTO> getAdminStats() {
        return ResponseEntity.ok(dashboardService.getAdminStats());
    }

    @GetMapping("/admin/etudiants")
    public ResponseEntity<List<EtudiantListDTO>> getEtudiantsList() {
        return ResponseEntity.ok(dashboardService.getEtudiantsList());
    }
    @GetMapping("/stats/status")
    public ResponseEntity<Map<String, Long>> getStatsByStatus() {
        return ResponseEntity.ok(dashboardService.getStatsByStatus());
    }

    @GetMapping("/evolution")
    public List<Map<String, Object>> getEvolution(
            @RequestParam(defaultValue = "6M") String period) {
        return dashboardService.getEvolution(period);
    }
}


