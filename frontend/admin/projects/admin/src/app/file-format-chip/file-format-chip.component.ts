import { Component, Input } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-file-format-chip',
  imports: [
    MatChipsModule
  ],
  templateUrl: './file-format-chip.component.html',
  styleUrl: './file-format-chip.component.less'
})
export class FileFormatChipComponent {
  @Input() formats: string[] = [];
}
