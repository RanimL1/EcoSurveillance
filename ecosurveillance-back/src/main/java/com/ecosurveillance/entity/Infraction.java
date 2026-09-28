package com.ecosurveillance.entity;

import com.ecosurveillance.enums.StatusInfraction;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "infractions")
@Data
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Infraction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "etudiant_id", nullable = false)
    private User etudiant;

    @Column(nullable = false)
    private String description;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(nullable = false)
    private LocalDateTime infractionDate;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private StatusInfraction status;

    @Column(name = "preuve_url")
    private String preuveUrl;

    @OneToOne
    @JoinColumn(name = "detection_id")
    private Detection detection;

    @OneToOne(mappedBy = "infraction", cascade = CascadeType.ALL)
    private PunitionAssignee punition;

    @PrePersist
    public void onCreate() {
        if (infractionDate == null) {
            infractionDate = LocalDateTime.now();
        }
        if (status == null) {
            status = StatusInfraction.EN_ATTENTE;
        }
    }
}