import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';
import { InfractionService } from '../../../services/infraction.service';
import { AuthService } from '../../../services/auth.service';
import { Infraction } from '../../../models/infraction.model';
import { PreuveService, Preuve } from '../../../services/preuve.service';

@Component({
  selector: 'app-my-infractions',
  standalone: true,
  imports: [CommonModule, RouterModule, ProofViewerComponent],
  templateUrl: './my-infractions.component.html',
  styleUrls: ['./my-infractions.component.css']
})
export class MyInfractionsComponent implements OnInit {

  infractions: Infraction[] = [];
  currentUser: any = null;
  user: any;
  selectedInfractionId: number | null = null;
  selectedInfractionPreuves: Preuve[] = [];
  loading = true;
  error: string | null = null;

  // ─── PARAMÈTRES DE PAGINATION ───
  currentPage: number = 1;
  pageSize: number = 6;
  protected readonly Math = Math; // Pour utiliser Math.min dans le HTML

  constructor(
    private infractionService: InfractionService,
    private authService: AuthService,
    private preuveService: PreuveService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.user = this.authService.getCurrentUser();
    this.loadInfractions();
  }

  loadInfractions(): void {
    this.loading = true;
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    this.infractionService.getInfractionsByEtudiant(user.id).subscribe({
      next: (res) => {
        this.infractions = res.map(i => ({
          ...i,
          status: i.status.toUpperCase() as 'EN_ATTENTE' | 'EN_COURS' | 'TERMINEE'
        }));
        this.loading = false;
      },
      error: () => {
        this.error = 'Impossible de charger vos infractions';
        this.loading = false;
      }
    });
  }

  // ─── LOGIQUE DE PAGINATION ───
  get paginatedInfractions(): Infraction[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.infractions.slice(start, start + this.pageSize);
  }

  get totalPages(): number {
    return Math.ceil(this.infractions.length / this.pageSize);
  }

  get pages(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }

  valider(infraction: Infraction): void {
    if (infraction.status === 'EN_ATTENTE') {
      infraction.status = 'EN_COURS';
      this.infractionService.updateStatus(infraction.id, 'EN_COURS').subscribe({
        next: (updated) => {
          const index = this.infractions.findIndex(i => i.id === infraction.id);
          if (index !== -1) this.infractions[index] = updated;
        },
        error: (err) => {
          console.error('Erreur validation infraction:', err);
          infraction.status = 'EN_ATTENTE';
        }
      });
    }
  }

  openProofs(id: number): void {
    this.selectedInfractionId = id;
    this.loadPreuves(id);
  }

  loadPreuves(infractionId: number): void {
    this.preuveService.getPreuvesByInfraction(infractionId).subscribe({
      next: (preuves) => this.selectedInfractionPreuves = preuves,
      error: (err) => {
        console.error('Erreur chargement preuves:', err);
        this.selectedInfractionPreuves = [];
      }
    });
  }

  closeModal(): void {
    this.selectedInfractionId = null;
    this.selectedInfractionPreuves = [];
  }

  onLogout(): void {
    this.authService.logout();
  }

  get showModal(): boolean {
    return this.selectedInfractionId !== null;
  }
}
