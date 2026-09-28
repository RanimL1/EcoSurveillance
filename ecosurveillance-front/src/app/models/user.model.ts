export interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  role: 'ADMIN' | 'ETUDIANT';
  dateCreation?: Date;
}
