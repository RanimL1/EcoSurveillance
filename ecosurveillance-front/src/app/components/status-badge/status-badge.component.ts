import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-badge.component.html',
  styleUrls: ['./status-badge.component.css']
})
export class StatusBadgeComponent {

  @Input() status: string = '';

  getBadgeClass(): string {
    switch (this.status.toUpperCase()) {
      case 'VALIDEE':
        return 'badge-success';
      case 'EN_ATTENTE':
        return 'badge-warning';
      case 'REJETEE':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  }
}
