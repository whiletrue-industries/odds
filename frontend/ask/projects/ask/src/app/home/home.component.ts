import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml, Title, Meta } from '@angular/platform-browser';
import { catchError, delay, filter, from, map, Subject, switchMap, tap, throttleTime, timer } from 'rxjs';
import { environment } from '../../environments/environment';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService, Deployment } from '../api.service';
import { SearchManager } from '../searcher';

@Component({
    selector: 'app-home',
    imports: [
        RouterModule,
        FormsModule,
    ],
    templateUrl: './home.component.html',
    styleUrl: './home.component.less'
})
export class HomeComponent {

  EXAMPLES = [
    'hmo license 51630',
    'fire risk assessment B12014FRA01',
    'what was the number of crimes in the Bloomsbury ward per year'
  ]

  @ViewChild('input') input: ElementRef<HTMLInputElement> | null = null;

  searcher: SearchManager;

  constructor(private api: ApiService, private sanitizer: DomSanitizer, 
              private route: ActivatedRoute, private router: Router, 
              private title: Title, private meta: Meta
            ) {
    this.searcher = new SearchManager(
      this.api,
      this.router,
      this.route,
      this.sanitizer,
      this.title, 
      this.meta
    );
  }

  ngAfterViewInit() {
    if (this.input) {
      this.searcher.inputElement = this.input.nativeElement;
    }
  }

  keydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      this.searcher.ask();
    }
  }

  get deployment_id() {
    return this.searcher.deployment_id;
  }

  get deployment() {
    return this.searcher.deployment;
  }
  
  get question() {
    return this.searcher.question;
  }

  get answer() {
    return this.searcher.answer;
  }

  get fullAnswer() {
    return this.searcher.fullAnswer;
  }

  get relatedQuestions() {
    return this.searcher.relatedQuestions;
  }
  
  get steps() {
    return this.searcher.steps;
  }

  get loading() {
    return this.searcher.loading;
  }
}
