import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml, Title, Meta } from '@angular/platform-browser';
import { catchError, filter, from, map, switchMap, tap, timer } from 'rxjs';
import { marked } from 'marked';
import { environment } from '../../environments/environment';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService, Deployment } from '../api.service';

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

  answer: SafeHtml | null = null;
  question: string = '';
  loading = false;
  relatedQuestions: { question: string, id: string }[] = [];
  deployment_id: string = '';
  deployment: Deployment | null = null;

  @ViewChild('input') input: ElementRef<HTMLInputElement> | null = null;

  constructor(private api: ApiService, private sanitizer: DomSanitizer, 
              private route: ActivatedRoute, private router: Router, 
              private title: Title, private meta: Meta
            ) {
    this.route.params.pipe(
      switchMap((params) => {
        this.deployment_id = params['deployment'];
        if (!params['id']) {
          this.clear()
        }
        if (this.deployment_id) {
          return this.api.getDeployment(this.deployment_id).pipe(
            map((deployment) => {
              this.deployment = deployment;
              this.title.setTitle(`Data Deep Search - ${deployment.agentOrgName}`);
              this.meta.updateTag({ name: 'description', content: `Ask Anything, and we'll try to locate the answer in ${deployment.agentCatalogDescriptions}` });
              return params;
            })
          )
        } else {
          return from([params]);
        }
      }),
      filter(params => !!params['id']),
      tap(() => {
        this.loading = true;
      }),
      switchMap(params => this.api.getAnswer(params['id'], undefined, this.deployment_id)),
      catchError((error) => {
        this.loading = false;
        this.router.navigate(['/', this.deployment_id]);
        return error;
      }),
    ).subscribe((data: any) => {
      this.question = data.question;
      this.relatedQuestions = data.related;
      this.setAnswer(data.answer);
      const shortQuestion = data.question.length > 100 ? data.question.slice(0, 100) + '…' : this.question;
      const shortAnswer = data.answer.length > 100 ? data.answer.slice(0, 100) + '…' : data.answer;
      this.title.setTitle(`${shortQuestion} | Data Deep Search - ${this.deployment?.agentOrgName || ''}`);
      this.meta.updateTag({ name: 'description', content: shortAnswer});
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
      this.api.getAnswer(undefined, this.question, this.deployment_id)
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
            this.router.navigate(['/' + this.deployment_id, 'a', response.id]);
          });
        },
      );
    }
  }

  clear() {
    this.router.navigate(['/', this.deployment_id]);
    this.question = '';
    this.answer = null;
    timer(100).subscribe(() => {
      if (this.input) {
        this.input.nativeElement.focus();
      }
    });
  }
}
