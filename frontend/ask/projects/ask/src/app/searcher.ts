import { DomSanitizer, Meta, SafeHtml, Title } from "@angular/platform-browser";
import { ActivatedRoute, Router } from "@angular/router";
import { catchError, delay, filter, from, map, Subject, switchMap, tap, throttleTime, timer } from "rxjs";
import { ApiService, Deployment } from "./api.service";
import { marked } from 'marked';

export const MESSAGES_EN = {
  'thinking': 'Thinking…',
  'getting ready': 'Getting ready…',
  'searching data sources': 'Searching data sources…',
  'fetching data source': 'Fetching data source…',
  'fetching dataset contents': 'Fetching dataset contents…',
  'analyzing dataset data': 'Analyzing dataset data…',
}

export const MESSAGES_HE = {
  'thinking': 'חושב…',
  'getting ready': 'מתכונן…',
  'searching data sources': 'מחפש מאגרי מידע',
  'fetching data source': 'מושך מאגר המידע…',
  'fetching dataset contents': 'מושך תוכן מסד הנתונים…',
  'analyzing dataset data': 'מנתח נתוני מסד הנתונים…',
}

export class SearchManager {

  answer: SafeHtml | null = null;
  question: string = '';
  loading = false;
  fullAnswer = false;
  relatedQuestions: { question: string, id: string }[] | null = null;
  steps: {kind: string, message: string}[] = [];
  currentId = '';
  deployment_id: string = '';
  deployment: Deployment | null = null;
  input: HTMLInputElement | null = null;

  partial: string = '';
  partialSubject = new Subject<string>();
  
  constructor(
    private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private sanitizer: DomSanitizer,
    private title: Title,
    private meta: Meta,
    private home = ['/'],
    private messages = MESSAGES_EN,
  ) {
    this.route.params.pipe(
      switchMap((params) => {
        console.log('ROUTE PARAMS', params);
        this.deployment_id = params['deployment'];
        if (!params['id']) {
          // console.log('CLEAR!');
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
      tap((params) => {
        this.loading = this.currentId !== params['id'];
      }),
      switchMap(params => this.api.getAnswer(params['id'], undefined, this.deployment_id)),
      catchError((error) => {
        this.loading = false;
        // console.log('NAVIGATE', error);
        this.router.navigate([...this.home, this.deployment_id]);
        return from([]);
      }),
    ).subscribe((data: any) => {
      this.question = data.question;
      this.updateTitleMetaAndAnswer(data);
    });
    this.partialSubject.pipe(
      map((t) => {
        this.partial += t;
        return this.partial;
      }),
      throttleTime(100, undefined, {leading: true, trailing: true}),
    ).subscribe((partial) => {
      this.setAnswer(partial, false);
    });
  }

  set inputElement(input: HTMLInputElement) {
    this.input = input;
  }

  setAnswer(answer: string, fullAnswer=true) {
    this.loading = fullAnswer;
    this.fullAnswer = fullAnswer;
    marked(answer, {async: true}).then((content) => {
      this.answer = this.sanitizer.bypassSecurityTrustHtml(content);
    });
  }

  ask(example?: string) {
    const question = example || this.question;
    if (question) {
      this.loading = true;
      this.partial = '';
      this.api.getAnswerStreaming(question, this.deployment_id)
      .pipe(        
        delay(0),
        catchError((error) => {
          console.log('ERROR CAUGHT', error);
          this.setAnswer('Error: ' + error.message);
          return from([]);
        })
      )
      .subscribe((msg) => {
        if (msg.type === 'text') {
          this.partialSubject.next(msg.value);
        } else if (msg.type === 'answer') {
          const value: any = msg.value;
          if (value.error) {
            this.setAnswer('Error: ' + value.error);
            return;
          }
          this.updateTitleMetaAndAnswer(value);
          // console.log('NAVIGATE', value.id);
          this.router.navigate([...this.home, this.deployment_id, 'a', value.id], {replaceUrl: true});
        } else if (msg.type === 'status') {
          const status = msg.value;
          if (status == 'preparing') {
            this.steps = [{kind: 'info', message: this.messages['getting ready']}];
          } else if (status == 'running') {
            this.steps = [{kind: 'info', message: this.messages['thinking']}];
          } else if (status == 'complete') {
            this.fullAnswer = true;
          }
        } else if (msg.type === 'tool') {
          const tool = msg.value.name;
          // const tool_args = msg.value.arguments;
            if (tool == 'search_datasets') {
                this.steps.push({kind: 'tool', message: this.messages['searching data sources']});
            } else if (tool == 'fetch_dataset') {
              this.steps.push({kind: 'tool', message: this.messages['fetching data source']});
            } else if (tool == 'fetch_resource') {
              this.steps.push({kind: 'tool', message: this.messages['fetching dataset contents']});
            } else if (tool == 'query_resource_database') {
              this.steps.push({kind: 'tool', message: this.messages['analyzing dataset data']});
            }
        }
      });
    }
  }

  // New method with added lines:
  private updateTitleMetaAndAnswer(data: any): void {
    this.relatedQuestions = data.related;
    this.currentId = data.id;
    this.setAnswer(data.answer);
    const shortQuestion = data.question.length > 100 ? data.question.slice(0, 100) + '…' : data.question;
    const shortAnswer = data.answer.length > 100 ? data.answer.slice(0, 100) + '…' : data.answer;
    this.title.setTitle(`${shortQuestion} | Data Deep Search - ${this.deployment?.agentOrgName || ''}`);
    this.meta.updateTag({ name: 'description', content: shortAnswer});
  }

  clear() {
    // console.log('NAVIGATE CLEAR');
    this.router.navigate([...this.home, this.deployment_id]);
    this.loading = false;
    this.question = '';
    this.answer = null;
    this.fullAnswer = false;
    this.relatedQuestions = null; 
    this.steps = [];
    timer(100).subscribe(() => {
      this.input?.focus();
    });
  }    
}