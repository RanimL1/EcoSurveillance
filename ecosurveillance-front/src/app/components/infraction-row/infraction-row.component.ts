import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-infraction-row',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './infraction-row.component.html',
  styleUrls: ['./infraction-row.component.css']
})
export class InfractionRowComponent {

  @Input() infraction: any;
  @Output() delete = new EventEmitter<number>();
  @Output() edit = new EventEmitter<any>();

  onDelete() {
    this.delete.emit(this.infraction.id);
  }

  onEdit() {
    this.edit.emit(this.infraction);
  }
}
