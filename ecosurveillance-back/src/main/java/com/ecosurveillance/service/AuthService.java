// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.AuthResponse;
// import com.ecosurveillance.dto.CreateUserRequest;
// import com.ecosurveillance.dto.LoginRequest;
// import com.ecosurveillance.entity.User;
// import com.ecosurveillance.repository.UserRepository;
// import com.ecosurveillance.security.JwtTokenProvider;
// import lombok.RequiredArgsConstructor;
// import org.springframework.security.crypto.password.PasswordEncoder;
// import org.springframework.stereotype.Service;

// @Service
// @RequiredArgsConstructor
// public class AuthService {

//     private final UserRepository userRepository;
//     private final PasswordEncoder passwordEncoder;
//     private final JwtTokenProvider jwtTokenProvider;

//     // =========================
//     // LOGIN
//     // =========================
//     public AuthResponse login(LoginRequest request) {

        
//         User user = userRepository.findByEmail(request.getEmail())
//                 .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
        
        
//         if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
//             throw new RuntimeException("Mot de passe incorrect");
//         }

//         // Générer le token JWT
//         String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole().name());

//         // Retourner les infos pour le frontend
//         AuthResponse response = new AuthResponse();
//         response.setToken(token);
//         response.setId(user.getId()); 
//         response.setEmail(user.getEmail());
//         response.setNom(user.getNom());
//         response.setRole(user.getRole());

//         return response;
//     }

//     // =========================
//     // REGISTER
//     // =========================
//     public User register(CreateUserRequest request) {
//         if (userRepository.existsByEmail(request.getEmail())) {
//             throw new RuntimeException("Email déjà utilisé");
//         }

//         User user = User.builder()
//                 .nom(request.getNom())
//                 .prenom(request.getPrenom()) // AJOUTEZ CETTE LIGNE
//                 .email(request.getEmail())
//                 .matricule(request.getMatricule())
//                 .password(passwordEncoder.encode(request.getPassword()))
//                 .role(request.getRole())
//                 .build();

//         return userRepository.save(user);
//     }
// }

// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.AuthResponse;
// import com.ecosurveillance.dto.CreateUserRequest;
// import com.ecosurveillance.dto.LoginRequest;
// import com.ecosurveillance.entity.User;
// import com.ecosurveillance.repository.UserRepository;
// import com.ecosurveillance.security.JwtTokenProvider;
// import lombok.RequiredArgsConstructor;
// import org.springframework.security.crypto.password.PasswordEncoder;
// import org.springframework.stereotype.Service;

// @Service
// @RequiredArgsConstructor

// public class AuthService {

//     private final UserRepository userRepository;
//     private final PasswordEncoder passwordEncoder;
//     private final JwtTokenProvider jwtTokenProvider;

//     // =========================
//     // LOGIN
//     // =========================
//     public AuthResponse login(LoginRequest request) {

        
//         User user = userRepository.findByEmail(request.getEmail())
//                 .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
        
        
//         if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
//             throw new RuntimeException("Mot de passe incorrect");
//         }

//         // Générer le token JWT
//         String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole().name());

//         // Retourner les infos pour le frontend
//         AuthResponse response = new AuthResponse();
//         response.setToken(token);
//         response.setId(user.getId()); 
//         response.setEmail(user.getEmail());
//         response.setNom(user.getNom());
//         response.setRole(user.getRole());

//         return response;
//     }

//     // =========================
//     // REGISTER
//     // =========================
//     public User register(CreateUserRequest request) {
//         if (userRepository.existsByEmail(request.getEmail())) {
//             throw new RuntimeException("Email déjà utilisé");
//         }

//         User user = User.builder()
//                 .nom(request.getNom())
//                 .prenom(request.getPrenom()) // AJOUTEZ CETTE LIGNE
//                 .email(request.getEmail())
//                 .matricule(request.getMatricule())
//                 .password(passwordEncoder.encode(request.getPassword()))
//                 .role(request.getRole())
//                 .build();

//         return userRepository.save(user);
//     }
// }

// package com.ecosurveillance.service;

// import com.ecosurveillance.dto.AuthResponse;
// import com.ecosurveillance.dto.CreateUserRequest;
// import com.ecosurveillance.dto.LoginRequest;
// import com.ecosurveillance.entity.User;
// import com.ecosurveillance.repository.UserRepository;
// import com.ecosurveillance.security.JwtTokenProvider;
// import lombok.RequiredArgsConstructor;
// import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
// import org.springframework.stereotype.Service;

// @Service
// @RequiredArgsConstructor
// public class AuthService {

//     private final UserRepository userRepository;
//     private final JwtTokenProvider jwtTokenProvider;
    
//     // Créer un encoder BCrypt directement
//     private final BCryptPasswordEncoder bCryptEncoder = new BCryptPasswordEncoder();

//     // =========================
//     // LOGIN
//     // =========================
//     public AuthResponse login(LoginRequest request) {
        
//         User user = userRepository.findByEmail(request.getEmail())
//                 .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
        
//         String storedPassword = user.getPassword();
//         String passwordToCheck = storedPassword;
        
//         // Convertir $2b$ en $2a$ pour compatibilité Python
//         if (storedPassword != null && storedPassword.startsWith("$2b$")) {
//             passwordToCheck = "$2a$" + storedPassword.substring(4);
//             System.out.println("✅ Conversion $2b$ → $2a$ effectuée");
//         }
        
//         // Vérifier le mot de passe
//         if (!bCryptEncoder.matches(request.getPassword(), passwordToCheck)) {
//             throw new RuntimeException("Mot de passe incorrect");
//         }

//         // Générer le token JWT
//         String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole().name());

//         // Retourner les infos pour le frontend
//         AuthResponse response = new AuthResponse();
//         response.setToken(token);
//         response.setId(user.getId()); 
//         response.setEmail(user.getEmail());
//         response.setNom(user.getNom());
//         response.setRole(user.getRole());

//         return response;
//     }

//     // =========================
//     // REGISTER
//     // =========================
//     public User register(CreateUserRequest request) {
//         if (userRepository.existsByEmail(request.getEmail())) {
//             throw new RuntimeException("Email déjà utilisé");
//         }

//         User user = User.builder()
//                 .nom(request.getNom())
//                 .prenom(request.getPrenom())
//                 .email(request.getEmail())
//                 .matricule(request.getMatricule())
//                 .password(bCryptEncoder.encode(request.getPassword()))
//                 .role(request.getRole())
//                 .build();

//         return userRepository.save(user);
//     }
// }

package com.ecosurveillance.service;

import com.ecosurveillance.dto.AuthResponse;
import com.ecosurveillance.dto.CreateUserRequest;
import com.ecosurveillance.dto.LoginRequest;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.repository.UserRepository;
import com.ecosurveillance.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;  // ← Gardez celui-ci injecté
    private final JwtTokenProvider jwtTokenProvider;

    // =========================
    // LOGIN
    // =========================
    public AuthResponse login(LoginRequest request) {
        
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
        
        // Le PasswordEncoder personnalisé de SecurityConfig gère déjà la conversion $2b$ → $2a$
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("Mot de passe incorrect");
        }

        // Générer le token JWT
        String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole().name());

        // Retourner les infos pour le frontend
        AuthResponse response = new AuthResponse();
        response.setToken(token);
        response.setId(user.getId()); 
        response.setEmail(user.getEmail());
        response.setNom(user.getNom());
        response.setRole(user.getRole());

        return response;
    }

    // =========================
    // REGISTER
    // =========================
    public User register(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new RuntimeException("Email déjà utilisé");
        }

        User user = User.builder()
                .nom(request.getNom())
                .prenom(request.getPrenom())
                .email(request.getEmail())
                .matricule(request.getMatricule())
                .password(passwordEncoder.encode(request.getPassword()))  // Utilise l'encodeur injecté
                .role(request.getRole())
                .build();

        return userRepository.save(user);
    }
}