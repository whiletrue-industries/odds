import { Component, computed } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { StateService } from '../state.service';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { ellipsizeText } from '../textUtils';
import { RtlizeDirective } from '../rtlize.directive';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';
import { QualityScoreComponent } from "../quality-score/quality-score.component";
import { FileFormatChipComponent } from "../file-format-chip/file-format-chip.component";
import { ResourceStatusChipComponent } from "../resource-status-chip/resource-status-chip.component";
import { marked } from 'marked';

@Component({
  selector: 'app-dataset',
  imports: [
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule,
    MatTabsModule,
    RtlizeDirective,
    QualityScoreComponent,
    FileFormatChipComponent,
    ResourceStatusChipComponent
],
  templateUrl: './dataset.component.html',
  styleUrl: './dataset.component.less'
})
export class DatasetComponent {

  columnsToDisplay = ['title', 'file_format', 'row_count', 'status', 'link'];
  ellipsizeText = ellipsizeText;

  description = computed<string | null>(() => {
    const dataset = this.state.dataset();
    if (dataset && dataset.description) {
      let description = dataset.description;
      description = description.replace(/```markdown/gi, '');
      description = description.replace(/```/gi, '');
      return marked(description);
    }
    return null;
  }); 

  constructor(private route: ActivatedRoute, public state: StateService) {
    this.state.updateFromRoute(this.route.snapshot)
  }
}
