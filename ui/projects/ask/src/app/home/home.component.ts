import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { catchError, filter, switchMap, tap, timer } from 'rxjs';
import { marked } from 'marked';
import { environment } from '../../environments/environment';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
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

  answer: SafeHtml | null = null;
  question: string = '';
  loading = false;
  relatedQuestions: { question: string, id: string }[] = [];

  @ViewChild('input') input: ElementRef<HTMLInputElement> | null = null;

  constructor(private http: HttpClient, private sanitizer: DomSanitizer, 
              private route: ActivatedRoute, private router: Router) {
    this.route.params.pipe(
      tap((params) => {
        if (!params['id']) {
          this.clear()
        }
      }),
      filter(params => !!params['id']),
      tap(() => {
        this.loading = true;
      }),
      switchMap(params => this.http.get(environment.endpoint, { params: {id: params['id'] }})),
      catchError((error) => {
        this.loading = false;
        this.router.navigate(['/']);
        return error;
      }),
    ).subscribe((data: any) => {
      this.question = data.question;
      this.relatedQuestions = data.related;
      this.setAnswer(data.answer);
    });
  }

  keydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      this.ask();
    }
  }

  setAnswer(answer: string) {
    this.loading = false;
    marked(answer, {async: true}).then((content) => {
      this.answer = this.sanitizer.bypassSecurityTrustHtml(content);
    });
  }

  ask() {
    if (this.question) {
      this.loading = true;
      this.http.get(environment.endpoint, { params: {q: this.question }})
      .pipe(
        catchError((error) => {
          this.setAnswer('Error: ' + error.message);
          return error;
        })
      )
      .subscribe(
        (response: any) => {
          if (response.error) {
            this.setAnswer('Error: ' + response.error);
            return;
          }
          marked(response.answer, {async: true}).then((content) => {
            this.setAnswer(content);
            this.router.navigate(['/a', response.id]);
          });
        },
      );
    }
  }

  clear() {
    this.router.navigate(['/']);
    this.question = '';
    this.answer = null;
    timer(100).subscribe(() => {
      if (this.input) {
        this.input.nativeElement.focus();
      }
    });
  }
}
