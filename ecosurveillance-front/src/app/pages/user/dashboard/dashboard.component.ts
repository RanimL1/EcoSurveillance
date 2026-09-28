import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InfractionService } from '../../../services/infraction.service';
import { CameraService } from '../../../services/camera.service';
import { AuthService } from '../../../services/auth.service';
import { StatsCardsComponent } from '../../../components/stats-cards/stats-cards.component';
import { InfractionTableComponent } from '../../../components/infraction-table/infraction-table.component';

@Component({
  selector: 'app-user-dashboard',
  standalone: true,
  imports: [CommonModule, StatsCardsComponent, InfractionTableComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  user: any;
  infractions: any[] = [];

  @ViewChild('video') video!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvas') canvas!: ElementRef<HTMLCanvasElement>;
  capturedImage: string = '';

  constructor(
    private infractionService: InfractionService,
    private cameraService: CameraService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.user = this.authService.getCurrentUser();
    this.loadUserInfractions();
  }

  // loadUserInfractions() {
  //   this.infractionService.getInfractions().subscribe((res: any[]) => {
  //     this.infractions = res;
  //   });
  // }
  loadUserInfractions() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  this.infractionService.getInfractionsByEtudiant(user.id).subscribe((res) => {
    this.infractions = res;
  });
}

  async startCamera() {
    await this.cameraService.startCamera(this.video.nativeElement);
  }

  stopCamera() {
    this.cameraService.stopCamera();
  }

  capture() {
    this.capturedImage = this.cameraService.captureImage(
      this.video.nativeElement,
      this.canvas.nativeElement
    );
  }
}
