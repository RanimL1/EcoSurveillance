import { User } from './user.model';

export interface Infraction {
  id: number;
  nom: string;        // ← adapté au DTO Java
  prenom: string;     // ← adapté au DTO Java
  etudiantEmail: string;
  date: string;
  status: 'EN_ATTENTE' | 'TERMINEE' | 'EN_COURS';
  preuves?: any[];
  punitionDescription?: string;
  punitionStatut?: string;
}
