import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../environments/environment';
import { from, Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  deployments: any = {};

  constructor(private http: HttpClient) { 
  }

  getDeployment(id: string): Observable<any> {
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
}
