import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DashboardService } from '../../../services/dashboard.service';
import { AuthService } from '../../../services/auth.service';
import { NgChartsModule } from 'ng2-charts';
import { Chart, ChartConfiguration, ChartData, registerables } from 'chart.js';

Chart.register(...registerables);

interface LocalDashboardStats {
  totalInfractions: number;
  infractionsAujourdhui: number;
  totalEtudiants: number;
  totalPunitions: number;
  punitionsAujourdhui: number;
  punitionsTerminees: number;
  camerasActives: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NgChartsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  currentUser: any = null;

  stats: LocalDashboardStats = {
    totalInfractions:     0,
    infractionsAujourdhui: 0,
    totalEtudiants:       0,
    totalPunitions:       0,
    punitionsAujourdhui:  0,
    punitionsTerminees:   0,
    camerasActives:       0
  };

  // ─── Bar Chart ────────────────────────────────────────────────────────────

  public barChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { precision: 0 },
        grid: { display: true }
      },
      x: { grid: { display: false } }
    }
  };

  public barChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: '#3b82f6',
      borderRadius: 5,
      borderSkipped: false
    }]
  };

  // ─── Pie Chart ────────────────────────────────────────────────────────────

  public pieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { boxWidth: 12, padding: 20 }
      }
    }
  };

  public pieChartData: ChartData<'pie'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: ['#3b82f6', '#f59e0b', '#ef4444', '#22c55e', '#a855f7']
    }]
  };

  loading: boolean = false;
  error: string = '';

  constructor(
    private dashboardService: DashboardService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.loadStats();
    this.loadEvolution();
    this.loadStatsByStatus();
  }

  // ─── KPIs ─────────────────────────────────────────────────────────────────

  loadStats(): void {
    this.loading = true;
    this.dashboardService.getDashboardStats().subscribe({
      next: (data) => {
        this.stats = {
          totalInfractions:      Number(data.totalInfractions      ?? 0),
          infractionsAujourdhui: Number(data.infractionsAujourdhui ?? 0),
          totalEtudiants:        Number(data.totalEtudiants        ?? 0),
          totalPunitions:        Number(data.totalPunitions        ?? 0),
          punitionsAujourdhui:   Number(data.punitionsAujourdhui   ?? 0),
          punitionsTerminees:    Number(data.punitionsTerminees     ?? 0),
          camerasActives:        Number(data.camerasActives         ?? 0)
        };
        this.loading = false;
      },
      error: (err) => {
        console.error('Erreur chargement stats', err);
        this.error = 'Impossible de charger les statistiques';
        this.loading = false;
      }
    });
  }

  // ─── Bar Chart : évolution ────────────────────────────────────────────────

  loadEvolution(): void {
    this.dashboardService.getEvolution().subscribe({
      next: (data) => {
        // LOG COMPLET pour identifier les clés exactes retournées par le backend
        console.log('=== EVOLUTION RAW ===', JSON.stringify(data));

        if (!data || data.length === 0) {
          console.warn('getEvolution() → tableau vide');
          return;
        }

        // Affiche les clés du premier élément pour diagnostic
        console.log('Clés disponibles :', Object.keys(data[0]));

        // Mapping défensif : on tente toutes les clés possibles
        const labels = data.map((d: any) =>
          d.semaine   ??   // { semaine: 'Sem 1', total: 5 }
          d.mois      ??   // { mois: 'Janvier', total: 5 }
          d.label     ??   // { label: 'Jan', total: 5 }
          d.periode   ??   // { periode: '2024-01', total: 5 }
          d.date      ??   // { date: '2024-01-01', total: 5 }
          d.week      ??   // { week: 'Week 1', total: 5 }
          d.month     ??   // { month: 'January', total: 5 }
          d.name      ??   // { name: 'Jan', total: 5 }
          String(d)        // fallback
        );

        const values = data.map((d: any) =>
          Number(
            d.total       ??   // { total: 5 }
            d.count       ??   // { count: 5 }
            d.nombre      ??   // { nombre: 5 }
            d.infractions ??   // { infractions: 5 }
            d.value       ??   // { value: 5 }
            d.nb          ??   // { nb: 5 }
            0
          )
        );

        console.log('Labels mappés :', labels);
        console.log('Valeurs mappées :', values);

        // Nouvelle référence d'objet → déclenche la détection ng2-charts
        this.barChartData = {
          labels,
          datasets: [{
            data: values,
            backgroundColor: '#3b82f6',
            borderRadius: 5,
            borderSkipped: false
          }]
        };

        this.cdr.detectChanges();
      },
      error: (err) => console.error('Erreur chargement évolution', err)
    });
  }

  // ─── Pie Chart : répartition par statut ──────────────────────────────────

  loadStatsByStatus(): void {
    this.dashboardService.getStatsByStatus().subscribe({
      next: (data) => {
        console.log('=== STATUS RAW ===', JSON.stringify(data));

        const labels = Object.keys(data).map(k =>
          k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
        );

        this.pieChartData = {
          labels,
          datasets: [{
            data: Object.values(data) as number[],
            backgroundColor: ['#3b82f6', '#f59e0b', '#ef4444', '#22c55e', '#a855f7']
          }]
        };

        this.cdr.detectChanges();
      },
      error: (err) => console.error('Erreur chargement statuts', err)
    });
  }

  // ─── Déconnexion ──────────────────────────────────────────────────────────

  onLogout(): void {
    this.authService.logout();
  }
}
