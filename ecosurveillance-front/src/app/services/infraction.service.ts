import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Infraction } from '../models/infraction.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class InfractionService {

  private apiUrl = `${environment.apiUrl}/infractions`;

  constructor(private http: HttpClient) {}

  // ─── Helper : token JWT depuis localStorage ───────────────────────────────
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('token') ?? '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getInfractions(): Observable<Infraction[]> {
    return this.http.get<Infraction[]>(this.apiUrl, { headers: this.getAuthHeaders() });
  }

  getInfractionById(id: number): Observable<Infraction> {
    return this.http.get<Infraction>(`${this.apiUrl}/${id}`, { headers: this.getAuthHeaders() });
  }

  createInfraction(infraction: Infraction): Observable<Infraction> {
    return this.http.post<Infraction>(this.apiUrl, infraction, { headers: this.getAuthHeaders() });
  }

  updateInfraction(id: number, infraction: Infraction): Observable<Infraction> {
    return this.http.put<Infraction>(`${this.apiUrl}/${id}`, infraction, { headers: this.getAuthHeaders() });
  }

  deleteInfraction(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`, { headers: this.getAuthHeaders() });
  }

  getInfractionsCount(): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/count`, { headers: this.getAuthHeaders() });
  }

  changerStatut(id: number, status: string): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/${id}/status?status=${status}`, {},
      { headers: this.getAuthHeaders() }
    );
  }

  validerPunition(id: number): Observable<any> {
    const token = localStorage.getItem('token');
    console.log('Token envoyé:', token); // ← vérifier ici
    return this.http.patch(
      `${this.apiUrl}/${id}/valider`, {},
      { headers: this.getAuthHeaders() }
    );
  }

  getInfractionsEnAttente(): Observable<Infraction[]> {
    return this.http.get<Infraction[]>(`${this.apiUrl}/status/EN_ATTENTE`, { headers: this.getAuthHeaders() });
  }

  getInfractionsValidees(): Observable<Infraction[]> {
    return this.http.get<Infraction[]>(`${this.apiUrl}/status/VALIDEE`, { headers: this.getAuthHeaders() });
  }

  getInfractionsByEtudiant(etudiantId: number): Observable<Infraction[]> {
    return this.http.get<Infraction[]>(`${this.apiUrl}/etudiant/${etudiantId}`, { headers: this.getAuthHeaders() });
  }

  updateStatus(id: number, status: string): Observable<Infraction> {
    return this.http.patch<Infraction>(
      `${this.apiUrl}/${id}/status?status=${status}`, {},
      { headers: this.getAuthHeaders() }
    );
  }

  getPreuves(infractionId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/preuves/${infractionId}`, { headers: this.getAuthHeaders() });
  }
}
