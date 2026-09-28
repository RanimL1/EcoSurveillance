import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class CameraService {

  private videoStream: MediaStream | null = null;

  constructor() {}

  async startCamera(videoElement: HTMLVideoElement): Promise<void> {
    try {
      this.videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoElement.srcObject = this.videoStream;
      await videoElement.play();
    } catch (err) {
      console.error('Impossible d’accéder à la caméra:', err);
    }
  }

  stopCamera(): void {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
  }

  captureImage(videoElement: HTMLVideoElement, canvasElement: HTMLCanvasElement): string {
    const context = canvasElement.getContext('2d');
    if (!context) return '';

    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

    // retourne l'image au format base64
    return canvasElement.toDataURL('image/png');
  }
}
