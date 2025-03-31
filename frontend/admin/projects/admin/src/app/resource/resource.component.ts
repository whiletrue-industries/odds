import { Component, computed } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { StateService } from '../state.service';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { marked } from 'marked';
import { Resource } from '../datatypes';
import { RtlizeDirective } from '../rtlize.directive';
import { MatButtonModule } from '@angular/material/button';
import { FileFormatChipComponent } from "../file-format-chip/file-format-chip.component";
import { ResourceStatusChipComponent } from "../resource-status-chip/resource-status-chip.component";
import { MatTabsModule } from '@angular/material/tabs';
import { QualityScoreComponent } from "../quality-score/quality-score.component";

@Component({
  selector: 'app-resource',
  imports: [
    RouterLink,
    MatIconModule,
    MatTableModule,
    MatButtonModule,
    MatTabsModule,
    RtlizeDirective,
    FileFormatChipComponent,
    ResourceStatusChipComponent,
],
  templateUrl: './resource.component.html',
  styleUrl: './resource.component.less'
})
export class ResourceComponent {

  JSON= JSON;
  resource = computed<Resource | null>(() => {
    const dataset = this.state.dataset();
    const resourceIdx = this.state.resourceIndex();
    if (dataset && resourceIdx !== null) {
      return dataset.resources[resourceIdx];
    }
    return null;
  });
  content = computed<string | null>(() => {
    const resource = this.resource();
    if (resource && resource.content) {
      let content = resource.content;
      content = content.replace(/```markdown/gi, '');
      content = content.replace(/```/gi, '');
      return marked(content);
    }
    return null;
  });

  fieldColumns = ['name', 'data_type', 'sample_values', 'missing_values_percent', 'max_value', 'min_value'];

  constructor(private route: ActivatedRoute, public state: StateService) {
    this.state.updateFromRoute(this.route.snapshot)
  }
}
