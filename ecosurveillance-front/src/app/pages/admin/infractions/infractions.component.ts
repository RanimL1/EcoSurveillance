import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { InfractionService } from '../../../services/infraction.service';
import { InfractionTableComponent } from '../../../components/infraction-table/infraction-table.component';
import { AuthService } from '../../../services/auth.service';
import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';

@Component({
  selector: 'app-infractions',
  standalone: true,
  imports: [CommonModule, RouterModule, InfractionTableComponent, ProofViewerComponent],
  templateUrl: './infractions.component.html',
  styleUrls: ['./infractions.component.css']
})
export class InfractionsComponent implements OnInit {
  infractions: any[] = [];
  loading = true;
  error: string | null = null;
  currentUser: any = null;
  selectedInfractionId: number | null = null;

  get showModal(): boolean {
    return this.selectedInfractionId !== null;
  }

  constructor(
    private infractionService: InfractionService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.loadInfractions();
  }

  loadInfractions(): void {
    this.loading = true;
    this.error = null;
    this.infractionService.getInfractions().subscribe({
      next: (res: any[]) => {
        this.infractions = res;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.error = 'Impossible de charger les infractions';
        this.loading = false;
      }
    });
  }

  editInfraction(infraction: any): void {
    console.log('Edit', infraction);
  }

  deleteInfraction(id: number): void {
    if (confirm('Supprimer cette infraction ?')) {
      this.infractionService.deleteInfraction(id).subscribe(() => {
        this.infractions = this.infractions.filter(i => i.id !== id);
      });
    }
  }

  onChangeStatus(id: number): void {
    this.infractionService.validerPunition(id).subscribe({
      next: () => {
        // CORRECTION : recharger depuis le serveur pour avoir punitionDescription à jour
        this.loadInfractions();
      },
      error: (err) => {
        console.error(err);
        this.error = 'Impossible de valider la punition';
      }
    });
  }

  openProofs(id: number): void {
    this.selectedInfractionId = id;
  }

  closeModal(): void {
    this.selectedInfractionId = null;
  }

  onLogout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.clear();
    this.router.navigate(['/login']);
  }
}
