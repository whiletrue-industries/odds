import { Component, computed } from '@angular/core';
import { ellipsizeText } from '../textUtils';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { marked } from 'marked';
import { FileFormatChipComponent } from '../file-format-chip/file-format-chip.component';
import { QualityScoreComponent } from '../quality-score/quality-score.component';
import { ResourceStatusChipComponent } from '../resource-status-chip/resource-status-chip.component';
import { RtlizeDirective } from '../rtlize.directive';
import { StateService } from '../state.service';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-webpage',
  imports: [
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule,
    MatTabsModule,
    RtlizeDirective,
],
  templateUrl: './webpage.component.html',
  styleUrl: './webpage.component.less'
})
export class WebpageComponent {

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
  content = computed<string | null>(() => {
    const resource = this.state.dataset()?.resources?.[0];
    if (resource && resource.content) {
      let content = resource.content;
      content = content.replace(/```markdown/gi, '');
      content = content.replace(/```/gi, '');
      return marked(content);
    }
    return null;
  });
  sourceLink = computed<SafeResourceUrl | null>(() => {
    const link = this.state.dataset()?.link;
    if (link) {
      return this.domSanitizer.bypassSecurityTrustResourceUrl(link);
    }
    return null;
  });

  constructor(private route: ActivatedRoute, public state: StateService, private domSanitizer: DomSanitizer) {
    this.state.updateFromRoute(this.route.snapshot)
  }
}