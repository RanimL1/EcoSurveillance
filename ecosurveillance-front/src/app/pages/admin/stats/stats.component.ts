import { Component, OnInit, OnDestroy, ChangeDetectorRef, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Chart, registerables } from 'chart.js';
import { DashboardService } from '../../../services/dashboard.service';
import { AuthService } from '../../../services/auth.service';
import { forkJoin, Subscription } from 'rxjs';

Chart.register(...registerables);

@Component({
  selector: 'app-stats',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './stats.component.html',
  styleUrls: ['./stats.component.css']
})
export class StatsComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('barChartRef') barChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('lineChartRef') lineChartRef!: ElementRef<HTMLCanvasElement>;

  barChart: any;
  lineChart: any;
  currentUser: any = null;
  selectedPeriod: string = '2M';
  viewReady = false;

  periods = [
    { value: '1M', label: '1 Mois' },
    { value: '2M', label: '2 Mois' },
    { value: '3M', label: '3 Mois' },
    { value: '6M', label: '6 Mois' }
  ];

  private dataSubscription?: Subscription;
  private statusData: any = null;
  private evolutionData: any[] = [];
  private dataReady = false;

  constructor(
    private dashboardService: DashboardService,
    private router: Router,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.loadStats();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    if (this.dataReady) {
      this.renderCharts();
    }
  }

  ngOnDestroy(): void {
    if (this.dataSubscription) this.dataSubscription.unsubscribe();
    this.destroyCharts();
  }

  loadStats(): void {
    if (this.dataSubscription) this.dataSubscription.unsubscribe();

    this.dataSubscription = forkJoin({
      status: this.dashboardService.getInfractionsByStatus(),
      evolution: this.dashboardService.getInfractionsEvolution(this.selectedPeriod)
    }).subscribe({
      next: ({ status, evolution }) => {
        this.statusData = status;
        this.evolutionData = evolution;
        this.dataReady = true;

        console.log('Evolution RAW:', JSON.stringify(evolution));

        if (this.viewReady) {
          this.renderCharts();
        }
      },
      error: (err) => console.error('Erreur API :', err)
    });
  }

  changePeriod(period: string): void {
    this.selectedPeriod = period;
    this.loadStats();
  }

  private renderCharts(): void {
    this.destroyCharts();
    setTimeout(() => {
      this.initBarChart();
      this.initLineChart();
    }, 200);
  }

  private initBarChart(): void {
    const canvas = this.barChartRef?.nativeElement
      ?? document.getElementById('barChart') as HTMLCanvasElement;
    if (!canvas) return;

    this.barChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: ['En attente', 'Terminée', 'En cours'],
        datasets: [{
          label: 'Infractions',
          data: [
            this.statusData?.en_attente ?? 0,
            this.statusData?.terminee   ?? 0,
            this.statusData?.en_cours   ?? 0
          ],
          backgroundColor: ['#ef4444', '#0F9D58', '#f59e0b'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  private initLineChart(): void {
    const canvas = this.lineChartRef?.nativeElement
      ?? document.getElementById('lineChart') as HTMLCanvasElement;
    if (!canvas) return;

    const labels = this.evolutionData.map((d: any) => String(d.periode ?? ''));
    const values = this.evolutionData.map((d: any) => Number(d.total ?? 0));

    // Pour 1M : dates journalières → on abrège le label (ex: "2026-03-27" → "27/03")
    const isDaily = this.selectedPeriod === '1M' || this.selectedPeriod === '2M';
    const displayLabels = isDaily
      ? labels.map(l => {
          const parts = l.split('-');
          return parts.length === 3 ? `${parts[2]}/${parts[1]}` : l;
        })
      : labels.map(l => {
          // Pour 3M/6M : "2026-03" → "Mars 26"
          const parts = l.split('-');
          if (parts.length === 2) {
            const mois = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc'];
            const m = parseInt(parts[1], 10) - 1;
            return `${mois[m]} ${parts[0].slice(2)}`;
          }
          return l;
        });

    this.lineChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: displayLabels,
        datasets: [{
          label: 'Évolution des infractions',
          data: values,
          borderColor: '#4285F4',
          backgroundColor: 'rgba(66, 133, 244, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: isDaily ? 2 : 4,  // points plus petits pour 30+ jours
          pointBackgroundColor: '#4285F4'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: {
            ticks: {
              maxRotation: isDaily ? 45 : 0,  // rotation pour éviter chevauchement
              autoSkip: true,
              maxTicksLimit: isDaily ? 15 : 6  // limite labels affichés
            }
          }
        }
      }
    });
  }

  private destroyCharts(): void {
    if (this.barChart)  { this.barChart.destroy();  this.barChart  = null; }
    if (this.lineChart) { this.lineChart.destroy();  this.lineChart = null; }
  }

  onLogout(): void {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
