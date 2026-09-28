package com.ecosurveillance.service;

import com.ecosurveillance.dto.UserDTO;
import com.ecosurveillance.entity.User;
import com.ecosurveillance.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.Base64;

@Service
@Transactional
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    private UserDTO toDTO(User user) {
        String photoBase64 = null;
        if (user.getPhotoData() != null) {
            photoBase64 = Base64.getEncoder().encodeToString(user.getPhotoData());
        }
        return UserDTO.builder()
                .id(user.getId())
                .nom(user.getNom())
                .prenom(user.getPrenom())
                .email(user.getEmail())
                .role(user.getRole())
                .matricule(user.getMatricule())
                .photoUrl(user.getPhotoUrl())
                .photoBase64(photoBase64)
                .build();
    }

    private User toEntity(UserDTO dto) {
        User user = new User();
        user.setId(dto.getId());
        user.setNom(dto.getNom());
        user.setPrenom(dto.getPrenom());
        user.setEmail(dto.getEmail());
        user.setRole(dto.getRole());
        user.setMatricule(dto.getMatricule());
        user.setPhotoUrl(dto.getPhotoUrl());
        if (dto.getPhotoBase64() != null) {
            user.setPhotoData(Base64.getDecoder().decode(dto.getPhotoBase64()));
        }
        return user;
    }

    public List<UserDTO> getAllUsers() {
        return userRepository.findAll().stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public UserDTO getUserById(Long id) {
        return userRepository.findById(id)
                .map(this::toDTO)
                .orElse(null);
    }

    public UserDTO createUser(UserDTO userDTO) {
        User user = toEntity(userDTO);
        User saved = userRepository.save(user);
        return toDTO(saved);
    }

    public UserDTO updateUser(Long id, UserDTO userDTO) {
        Optional<User> optionalUser = userRepository.findById(id);
        if (optionalUser.isEmpty()) return null;

        User user = optionalUser.get();
        user.setNom(userDTO.getNom());
        user.setPrenom(userDTO.getPrenom());
        user.setEmail(userDTO.getEmail());
        user.setRole(userDTO.getRole());
        user.setMatricule(userDTO.getMatricule());
        if (userDTO.getPhotoBase64() != null) {
            user.setPhotoData(Base64.getDecoder().decode(userDTO.getPhotoBase64()));
        }
        user.setPhotoUrl(userDTO.getPhotoUrl());

        return toDTO(userRepository.save(user));
    }

    public boolean deleteUser(Long id) {
        if (!userRepository.existsById(id)) return false;
        userRepository.deleteById(id);
        return true;
    }
}