import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatusBadgeComponent } from '../../../components/status-badge/status-badge.component';

interface Camera {
  id: number;
  nom: string;
  description?: string;
  statut?: string;
}

@Component({
  selector: 'app-cameras',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  templateUrl: './cameras.component.html',
  styleUrls: ['./cameras.component.css']
})
export class CamerasComponent implements OnInit {

  cameras: Camera[] = [];
  selectedCamera: Camera | null = null;

  constructor() {}

  ngOnInit(): void {
    this.loadCameras();
  }

  loadCameras() {
    this.cameras = [
      { id: 1, nom: 'Caméra Entrée', description: 'Entrée principale', statut: 'EN_LIGNE' },
      { id: 2, nom: 'Caméra Jardin', description: 'Surveillance jardin', statut: 'HORS_LIGNE' },
    ];
  }

  editCamera(camera: Camera) {
    this.selectedCamera = { ...camera };
  }

  deleteCamera(cameraId: number) {
    this.cameras = this.cameras.filter(c => c.id !== cameraId);
  }

  addCamera() {
    const newId = this.cameras.length + 1;
    this.cameras.push({ id: newId, nom: `Nouvelle Caméra ${newId}`, statut: 'HORS_LIGNE' });
  }

  testCamera(camera: Camera) {
    console.log('Test caméra:', camera.nom);
  }
}
