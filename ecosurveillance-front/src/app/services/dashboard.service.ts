import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface DashboardStatsDTO {
  totalInfractions: number;
  infractionsAujourdhui: number;
  totalEtudiants: number;
  totalPunitions: number;
  punitionsAujourdhui: number;
  punitionsTerminees: number;
  camerasActives: number;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private apiUrl = 'http://localhost:8081/api/dashboard';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken() ?? '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  // GET /api/dashboard/admin/stats
  getDashboardStats(): Observable<DashboardStatsDTO> {
    return this.http.get<DashboardStatsDTO>(
      `${this.apiUrl}/admin/stats`,
      { headers: this.getAuthHeaders() }
    );
  }

  // GET /api/dashboard/stats/status
  getStatsByStatus(): Observable<{ [key: string]: number }> {
    return this.http.get<{ [key: string]: number }>(
      `${this.apiUrl}/stats/status`,
      { headers: this.getAuthHeaders() }
    );
  }

  getInfractionsByStatus(): Observable<{ [key: string]: number }> {
    return this.getStatsByStatus();
  }

  // GET /api/dashboard/evolution?period=2M
  // CORRECTION : /stats/evolution → /evolution (URL exacte du controller Java)
  getEvolution(period: string = '6M'): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/evolution?period=${period}`,
      { headers: this.getAuthHeaders() }
    );
  }

  getInfractionsEvolution(period: string = '6M'): Observable<any[]> {
    return this.getEvolution(period);
  }
}
