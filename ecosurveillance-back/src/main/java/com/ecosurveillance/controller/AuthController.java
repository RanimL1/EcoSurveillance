package com.ecosurveillance.controller;

import com.ecosurveillance.dto.AuthResponse;
import com.ecosurveillance.dto.CreateUserRequest;
import com.ecosurveillance.dto.LoginRequest;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @PostMapping("/register")
    public ResponseEntity<User> register(@RequestBody CreateUserRequest request) {
        return ResponseEntity.ok(authService.register(request));
    }
}