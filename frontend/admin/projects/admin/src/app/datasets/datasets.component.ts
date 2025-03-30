import { Component, effect, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DataCatalog, Dataset } from '../datatypes';
import { ApiService } from '../api.service';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatSortModule, Sort } from '@angular/material/sort';
import { StateService } from '../state.service';
import { ellipsizeText } from '../textUtils';
import { RtlizeDirective } from '../rtlize.directive';
import { QualityScoreComponent } from "../quality-score/quality-score.component";
import { MatButtonModule } from '@angular/material/button';
import { FileFormatChipComponent } from "../file-format-chip/file-format-chip.component";

@Component({
  selector: 'app-datasets',
  imports: [
    RouterLink,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatPaginatorModule,
    MatChipsModule,
    MatSortModule,
    RtlizeDirective,
    QualityScoreComponent,
    FileFormatChipComponent
],
  templateUrl: './datasets.component.html',
  styleUrl: './datasets.component.less'
})
export class DatasetsComponent {

  totalDatasets = signal<number | null>(null);
  datasets = signal<Dataset[]>([]);

  columnsToDisplay = ['title', 'publisher', 'quality_score'];
  columnsToDisplay2 = ['description', 'resource_formats', 'link'];

  ellipsizeText = ellipsizeText;

  FIELD_TO_SORT: { [key: string]: string } = {
    title: 'title.keyword',
    publisher: 'publisher.keyword',
    quality_score: 'quality_score',
  };

  constructor(private route: ActivatedRoute, private api: ApiService, public state: StateService) {

    this.state.updateFromRoute(this.route.snapshot)

    effect(() => {
      const deploymentId = this.state.deploymentId();
      const catalogId = this.state.catalogId();
      if (catalogId && deploymentId) {
        this.totalDatasets.set(null);
        this.datasets.set([]);
      } 
    });

    effect(() => {
      const deploymentId = this.state.deploymentId();
      const catalogId = this.state.catalogId();
      const page = this.state.currentPage();
      const sort = this.state.currentSortDirective();
      console.log('Page/sort changed:', deploymentId, catalogId, page, 'Sort:', sort);
      if (catalogId && deploymentId && page) {
        this.api.getDatasets(deploymentId, catalogId, page, sort).subscribe((result) => {
          this.datasets.set(result.datasets);
          this.totalDatasets.set(result.total);
        });
      } else {
        this.datasets.set([]);
      }
    });
  }

  onPageChange(event: PageEvent): void {
    this.state.currentPage.set(event.pageIndex + 1);
  }

  resourceFormats(dataset: Dataset): string[] {
    // Returns unique set of file formats for the dataset
    if (dataset.resources && dataset.resources.length > 0) {
      return Array.from(new Set(dataset.resources.map(resource => resource.file_format).filter(format => !!format)));
    }
    return [];
  }

  onSort(sort: Sort): void {
    // Handle sorting here
    console.log('Sorting:', sort);
    if (sort.direction === '') {
      // Reset sort
      this.state.currentSortDirective.set(this.state.defaultSort);
    } else if (sort.active) {
      const dir = sort.direction === 'asc' ? '+' : '-';
      const field = this.FIELD_TO_SORT[sort.active];
      this.state.currentSortDirective.set(`${dir}${field}`);
    }
    this.state.currentSort.set(sort);
  }
}
