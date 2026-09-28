package com.ecosurveillance.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "detections")
@Data
@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Detection {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String type;  // "littering" pour votre cas
    
    @Column(name = "detected_at")
    private LocalDateTime detectedAt;
    
    private boolean confirmed;
    
    @Column(name = "track_id")
    private Integer trackId;  // ID du tracker DeepSORT
    
    @Column(name = "capture_path")
    private String capturePath;  // Chemin de l'image capturée

    @Column(name = "video_path")
    private String videoPath;   
    
    @Column(name = "bbox_coordinates")
    private String bboxCoordinates;  // Stocker [x1,y1,x2,y2] en JSON
    
    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;
    
    @OneToOne(mappedBy = "detection", cascade = CascadeType.ALL)
    private Infraction infraction;
    
    @PrePersist
    public void onCreate() {
        if (detectedAt == null) {
            detectedAt = LocalDateTime.now();
        }
    }
}