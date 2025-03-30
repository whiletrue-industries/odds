import { Component, Input } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-resource-status-chip',
  imports: [
    MatChipsModule
  ],
  templateUrl: './resource-status-chip.component.html',
  styleUrl: './resource-status-chip.component.less'
})
export class ResourceStatusChipComponent {
  @Input() status: string = '';
}
