package com.ecosurveillance.dto;

import com.ecosurveillance.enums.Role;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class UserDTO {
    private Long id;
    private String nom;
    private String prenom;
    private String email;
    private Role role;
    private String matricule;
    private String photoUrl;
    private String photoBase64;

    public String getFullName() {
        if (prenom != null && nom != null) {
            return prenom + " " + nom;
        }
        return nom != null ? nom : "";
    }
}