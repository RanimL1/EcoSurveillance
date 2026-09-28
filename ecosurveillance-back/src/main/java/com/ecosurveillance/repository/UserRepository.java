package com.ecosurveillance.repository;

import com.ecosurveillance.entity.User;
import com.ecosurveillance.enums.Role;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);
    long countByRole(Role role);
    List<User> findByRole(Role role);
}