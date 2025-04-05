import { AfterViewInit, Component, effect, signal, ViewChild } from '@angular/core';
import { Dataset, QA } from '../datatypes';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSortModule, MatSort, Sort } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { timer } from 'rxjs';
import { ApiService } from '../api.service';
import { RtlizeDirective } from '../rtlize.directive';
import { StateService } from '../state.service';
import { TextFilterComponent } from '../text-filter/text-filter.component';
import { ellipsizeText } from '../textUtils';
import { QualityScoreComponent } from "../quality-score/quality-score.component";
import { marked } from 'marked';
import dayjs from 'dayjs';

@Component({
  selector: 'app-questions',
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
    TextFilterComponent,
    QualityScoreComponent
],
  templateUrl: './questions.component.html',
  styleUrl: './questions.component.less'
})
export class QuestionsComponent implements AfterViewInit {

  totalQuestions = signal<number | null>(null);
  questions = signal<QA[]>([]);

  ellipsizeText = ellipsizeText;
  marked = marked;

  FIELD_TO_SORT: { [key: string]: string } = {
    timestamp: 'last_updated',
    success: 'success',
    score: 'score',
  };
  @ViewChild(MatSort) matSort: MatSort;

  firstRowColumns = ['timestamp', 'success', 'score', 'link'];
  middleRowColumns = ['question'];
  lastRowColumns = ['answer'];

  constructor(private route: ActivatedRoute, private api: ApiService, public state: StateService) {

    this.state.updateFromRoute(this.route.snapshot)

    effect(() => {
      const deploymentId = this.state.deploymentId();
      const catalogId = this.state.catalogId();
      if (catalogId && deploymentId) {
        this.totalQuestions.set(null);
        this.questions.set([]);
      } 
    });

    effect(() => {
      const deploymentId = this.state.deploymentId();
      const page = this.state.questionsPage.currentPage();
      const sort = this.state.questionsPage.currentSortDirective();
      const textFilter = this.state.questionsPage.textFilter();
      console.log('Page/sort changed:', deploymentId, page, 'Sort:', sort);
      if (deploymentId && page) {
        this.api.getQuestions(deploymentId, page, sort, textFilter).subscribe((result) => {
          this.questions.set(result.questions);
          this.totalQuestions.set(result.total);
        });
      } else {
        this.questions.set([]);
      }
    });
  }

  ngAfterViewInit(): void {
    const sort = this.state.questionsPage.currentSort();
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
    this.state.questionsPage.currentPage.set(event.pageIndex + 1);
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
    this.state.questionsPage.currentSort.set(sort);
    if (sort.direction === '') {
      // Reset sort
      this.state.questionsPage.currentSortDirective.set(null);
    } else if (sort.active) {
      const dir = sort.direction === 'asc' ? '+' : '-';
      const field = this.FIELD_TO_SORT[sort.active];
      console.log('Sorting2:', `${dir}${field}`);
      this.state.questionsPage.currentSortDirective.set(`${dir}${field}`);
    }
  }

  formatDate(date: string): string {
    if (!date) {
      return '';
    }
    return dayjs(date).local().format('DD/MM/YYYY HH:MM');
  }
}
