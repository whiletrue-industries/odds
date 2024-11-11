import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { catchError, timer } from 'rxjs';
import { marked } from 'marked';

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

  @ViewChild('input') input: ElementRef<HTMLInputElement> | null = null;

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) { }

  keydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      this.ask();
    }
  }

  ask() {
    if (this.question) {
      this.loading = true;
      const encoded = encodeURIComponent(this.question);
      this.http.get('/answer', { params: {q: encoded }})
      .pipe(
        catchError((error) => {
          this.answer = 'Error: ' + error.message;
          this.loading = false;
          return error;
        })
      )
      .subscribe(
        (response: any) => {
          if (response.error) {
            this.answer = 'Error: ' + response.error;
            this.loading = false;
            return;
          }
          marked(response.answer, {async: true}).then((content) => {
            this.answer = this.sanitizer.bypassSecurityTrustHtml(content);
            this.loading = false;
          });
        },
      );
    }
  }

  clear() {
    this.question = '';
    this.answer = null;
    timer(100).subscribe(() => {
      if (this.input) {
        this.input.nativeElement.focus();
      }
    });
  }
}
