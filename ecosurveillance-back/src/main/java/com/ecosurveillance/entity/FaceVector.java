package com.ecosurveillance.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "face_vectors")
@Data
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FaceVector {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String vector;

    @OneToOne
    @JoinColumn(name = "user_id", unique = true)
    private User user;
}