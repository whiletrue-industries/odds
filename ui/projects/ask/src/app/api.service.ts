import { HttpClient } from '@angular/common/http';
import { Injectable, NgZone } from '@angular/core';
import { environment } from '../environments/environment';
import { from, Observable, tap } from 'rxjs';

export type Deployment = {
  id: string,
  catalogIds: string[],
  agentOrgName: string,
  agentCatalogDescriptions: string,
  uiLogoHtml: string,
  uiDisplayHtml: string,
  examples: string[],
};

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  deployments: any = {};

  constructor(private http: HttpClient, private zone: NgZone) { 
  }

  getDeployment(id: string): Observable<Deployment> {
    if (this.deployments[id]) {
      return from([this.deployments[id]]);
    } else {
      return this.http.get(`${environment.configEndpoint}/${id}`).pipe(
        tap((deployment: any) => {
          this.deployments[deployment.id] = deployment;
        })
      );
    }
  }

  getAnswer(id: string | undefined, q: string | undefined, deployment_id: string): Observable<any> {
    const params: any = {deployment_id};
    if (id) {
      params['id'] = id;
    }
    if (q) {
      params['q'] = q;
    }
    return this.http.get(environment.endpoint, {params});
  }

  getAnswerStreaming(q: string, deployment_id: string): Observable<any> {
    // Use SSE to get streaming answers
    return new Observable(observer => {
      const params: any = {deployment_id, q};
      const url = `${environment.endpointStreaming}?${new URLSearchParams(params).toString()}`;
      const eventSource = new EventSource(url);
      eventSource.onmessage = (event) => {
        // console.log('EVENT', event);
        try {
          this.zone.run(() => {
            observer.next(JSON.parse(event.data));
          });
        } catch (error) {
          console.error('PARSE ERROR', error);
          observer.error(error);
        }
      };
      eventSource.onerror = (error) => {
        console.error('EVENTSOURCE ERROR', error);
        eventSource.close(); //
        observer.complete();
        // observer.error(error);
      };
      return () => {
        eventSource.close();
      };
    });
  }
}
