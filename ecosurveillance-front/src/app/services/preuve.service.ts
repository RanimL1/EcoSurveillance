import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Preuve {
  id: number;
  type: 'image' | 'video';
  url: string;
}

@Injectable({
  providedIn: 'root'
})
export class PreuveService {

  private apiUrl = `${environment.apiUrl}/preuves`;

  constructor(private http: HttpClient) {}

  getPreuvesByInfraction(infractionId: number) {
    return this.http.get<Preuve[]>(`${this.apiUrl}/infraction/${infractionId}`);
  }

  getPreuvesByNomAndDate(nom: string, date: string): Observable<Preuve[]> {
    return this.http.get<Preuve[]>(
      `${this.apiUrl}/search?nom=${nom}&date=${date}`
    );
  }
}