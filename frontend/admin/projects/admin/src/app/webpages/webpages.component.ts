import { AfterViewInit, Component, effect, signal, ViewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DataCatalog, Dataset } from '../datatypes';
import { ApiService } from '../api.service';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatSort, MatSortModule, Sort } from '@angular/material/sort';
import { StateService } from '../state.service';
import { ellipsizeText } from '../textUtils';
import { RtlizeDirective } from '../rtlize.directive';
import { MatButtonModule } from '@angular/material/button';
import { TextFilterComponent } from "../text-filter/text-filter.component";
import { timer } from 'rxjs';

@Component({
  selector: 'app-webpages',
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
    TextFilterComponent
],
  templateUrl: './webpages.component.html',
  styleUrl: './webpages.component.less'
})
export class WebpagesComponent implements AfterViewInit {

  totalDatasets = signal<number | null>(null);
  datasets = signal<Dataset[]>([]);

  columnsToDisplay = ['title', 'link'];
  columnsToDisplay2 = ['better_description'];

  ellipsizeText = ellipsizeText;

  FIELD_TO_SORT: { [key: string]: string } = {
    title: 'title.keyword',
    publisher: 'publisher.keyword',
    quality_score: 'quality_score',
  };
  @ViewChild(MatSort) matSort: MatSort;

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
      const page = this.state.webpagesPage.currentPage();
      const sort = this.state.webpagesPage.currentSortDirective();
      const textFilter = this.state.webpagesPage.textFilter();
      console.log('Page/sort changed:', deploymentId, catalogId, page, 'Sort:', sort);
      if (catalogId && deploymentId && page) {
        this.api.getDatasets(deploymentId, catalogId, page, sort, textFilter).subscribe((result) => {
          this.datasets.set(result.datasets);
          this.totalDatasets.set(result.total);
        });
      } else {
        this.datasets.set([]);
      }
    });
  }

  ngAfterViewInit(): void {
    const sort = this.state.webpagesPage.currentSort();
    timer(0).subscribe(() => {
      if (sort) {
        this.matSort.sort({
          id: sort.active,
          start: sort.direction,
          disableClear: false
        });
      };
    });
  }

  onPageChange(event: PageEvent): void {
    this.state.webpagesPage.currentPage.set(event.pageIndex + 1);
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
    this.state.webpagesPage.currentSort.set(sort);
    if (sort.direction === '') {
      // Reset sort
      this.state.webpagesPage.currentSortDirective.set(null);
    } else if (sort.active) {
      const dir = sort.direction === 'asc' ? '+' : '-';
      const field = this.FIELD_TO_SORT[sort.active];
      this.state.webpagesPage.currentSortDirective.set(`${dir}${field}`);
    }
  }
}
