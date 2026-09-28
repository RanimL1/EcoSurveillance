package com.ecosurveillance.dto;

import com.ecosurveillance.enums.Role;
import lombok.Data;

@Data
public class AuthResponse {
    private Long id;  
    private String token;
    private String email;
    private String nom;
    private Role role;
}
