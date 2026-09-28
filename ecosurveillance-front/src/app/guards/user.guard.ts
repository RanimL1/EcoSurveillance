import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class UserGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {

    // Vérifier si l'utilisateur est connecté
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
      return false;
    }

    // Vérifier le rôle USER / ETUDIANT
    const role = this.authService.getUserRole();

    if (role === 'ETUDIANT' ) {
      return true;
    }

    // Sinon redirection
    this.router.navigate(['/unauthorized']);
    return false;
  }
}
