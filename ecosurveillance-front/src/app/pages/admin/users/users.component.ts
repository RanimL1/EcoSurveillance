import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css']
})
export class UsersComponent implements OnInit {

  users: any[] = [];
  adminUser: any = null;

  constructor(
    private http: HttpClient,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.adminUser = this.authService.getCurrentUser();
    this.loadUsers();
  }

  loadUsers(): void {
    const token = this.authService.getToken() ?? '';
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.get<any[]>('http://localhost:8081/api/dashboard/admin/etudiants', { headers })
      .subscribe({
        next: (res) => this.users = res,
        error: (err) => console.error('Erreur chargement étudiants', err)
      });
  }

  onLogout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.clear();
    this.router.navigate(['/login']);
  }
}
