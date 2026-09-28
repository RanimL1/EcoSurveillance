import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Infraction } from '../../models/infraction.model';

@Component({
  selector: 'app-infraction-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './infraction-table.component.html',
  styleUrls: ['./infraction-table.component.css']
})
export class InfractionTableComponent {
  protected readonly Math = Math;
  @Input() infractions: any[] = [];
  @Input() readOnly: boolean = false;
  @Output() edit = new EventEmitter<any>();
  @Output() delete = new EventEmitter<number>();
  @Output() changeStatus = new EventEmitter<number>();
  @Output() viewProofs = new EventEmitter<number>();

  // ─── Filtre ───────────────────────────────────────────────────────────────
  selectedStatus: string = 'TOUS';

  get countTous()      { return this.infractions.length; }
  get countEnAttente() { return this.infractions.filter(i => i.status === 'EN_ATTENTE').length; }
  get countEnCours()   { return this.infractions.filter(i => i.status === 'EN_COURS').length; }
  get countTerminee()  { return this.infractions.filter(i => i.status === 'TERMINEE').length; }

  get filteredInfractions(): any[] {
    const filtered = this.selectedStatus === 'TOUS'
      ? this.infractions
      : this.infractions.filter(i => i.status === this.selectedStatus);

    // Paginer les résultats filtrés
    const start = (this.currentPage - 1) * this.pageSize;
    return filtered.slice(start, start + this.pageSize);
  }

  get totalFiltered(): number {
    if (this.selectedStatus === 'TOUS') return this.infractions.length;
    return this.infractions.filter(i => i.status === this.selectedStatus).length;
  }

  // ─── Pagination ───────────────────────────────────────────────────────────
  currentPage: number = 1;
  pageSize: number = 6;

  get totalPages(): number {
    return Math.ceil(this.totalFiltered / this.pageSize);
  }

  get pages(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }

  // Reset page quand on change de filtre
  setStatus(status: string): void {
    this.selectedStatus = status;
    this.currentPage = 1;
  }

  // ─── Méthodes existantes ──────────────────────────────────────────────────

  getNomComplet(infraction: Infraction): string {
    if (infraction.nom || infraction.prenom) {
      return `${infraction.prenom || ''} ${infraction.nom || ''}`.trim();
    }
    return '-';
  }

  onEdit(infraction: any) {
    if (!this.readOnly) this.edit.emit(infraction);
  }

  onDelete(id: number) {
    if (!this.readOnly) this.delete.emit(id);
  }

  onChangeStatus(event: Event, id: number) {
    event.stopPropagation();
    this.changeStatus.emit(id);
  }

  openProofs(id: number): void {
    this.viewProofs.emit(id);
  }
}
