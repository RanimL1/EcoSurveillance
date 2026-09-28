import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';
import { RouterModule, Router } from '@angular/router';
import { InfractionService } from '../../../services/infraction.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterModule, ProofViewerComponent],
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {

  infractions: any[] = [];
  user: any;

  totalInfractions = 0;
  terminees = 0;
  enAttente = 0;
  prochainePunition: string = '-';

  showModal = false;
  selectedInfractionId: number | null = null;

  constructor(
    private router: Router,
    private infractionService: InfractionService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.user = this.authService.getCurrentUser();
    this.loadInfractions();
  }

  loadInfractions(): void {
    const user = this.authService.getCurrentUser();
    if (!user) return;

    this.infractionService.getInfractionsByEtudiant(user.id).subscribe((res: any[]) => {

      // ✅ Conversion du champ "date" (nom réel backend) → infractionDate en Date object
      this.infractions = res.map(i => ({
        ...i,
        infractionDate: i.date ? new Date(i.date) : null
      }));

      this.totalInfractions = this.infractions.length;
      this.terminees = this.infractions.filter(i => i.status === 'TERMINEE').length;
      this.enAttente = this.infractions.filter(i => i.status === 'EN_ATTENTE').length;

      // ✅ Utilise infractionDate déjà converti
      const dates = this.infractions
        .filter(i => i.status === 'EN_ATTENTE' && i.infractionDate)
        .map(i => i.infractionDate as Date)
        .sort((a, b) => a.getTime() - b.getTime());

      this.prochainePunition = dates.length > 0
        ? dates[0].toLocaleDateString('fr-FR')
        : '-';
    });
  }

  onLogout(): void {
    this.authService.logout();
  }

  openProofs(id: number) {
    this.selectedInfractionId = id;
    this.showModal = true;
  }

  closeModal() {
    this.showModal = false;
    this.selectedInfractionId = null;
  }
}
