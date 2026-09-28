import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stats-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-cards.component.html',
  styleUrls: ['./stats-cards.component.css']
})
export class StatsCardsComponent implements OnChanges {

  @Input() stats: any = null;

  // fallback sécurisé
  safeStats = {
    totalInfractions: 0,
    totalPunitions: 0,
    infractionsParType: {}
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['stats'] && this.stats) {
      this.safeStats = {
        totalInfractions: this.stats.totalInfractions ?? 0,
        totalPunitions: this.stats.totalPunitions ?? 0,
        infractionsParType: this.stats.infractionsParType ?? {}
      };
    }
  }
}
