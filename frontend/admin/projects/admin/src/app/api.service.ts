import { computed, effect, Injectable, signal } from '@angular/core';
import { AuthService } from './auth.service';
import { filter, forkJoin, from, map, Observable, switchMap, tap } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment.development';
import { DataCatalog, Dataset, Deployment } from './datatypes';
import { Router } from '@angular/router';

export type DatasetResult = {
  datasets: Dataset[],
  total: number,
  pages: number,
  page: number
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  token = signal<string | null>(null);
  deployments = signal<Deployment[]>([]);
  currentDeployment = signal<Deployment | null>(null);
  dataCatalogs = signal<DataCatalog[]>([]);
  catalogDatasetCount = signal<{ [key: string]: number }>({});
  websites = computed<DataCatalog[]>(() => {
    const websites = this.dataCatalogs().filter((catalog) => {
      return catalog.kind === 'website';
    });
    console.log('Websites:', websites);
    return websites;
  });
  catalogs = computed<DataCatalog[]>(() => {
    const catalogs = this.dataCatalogs().filter((catalog) => {
      return catalog.kind !== 'website';
    });
    console.log('Catalogs:', catalogs);
    return catalogs;
  });
  requestedDeploymentId: string | null = null;

  constructor(private auth: AuthService, private http: HttpClient, private router: Router) {
    this.auth.user.pipe(
      tap(user => {
        if (!user) {
          console.log('User is not logged in');
          this.token.set(null);
          router.navigate(['/login']);
        }
      }),
      filter(user => !!user),
      switchMap(user => {
        const authToken = user.getIdToken();
        return authToken;
      }),
    ).subscribe((token) => {
      this.token.set(token);
    });

    // effect(() => {
    //   const dep = this.currentDeployment();
    // });

    effect(() => {
      if (this.token()) {
        this.loadDeployments().subscribe((result) => {
          this.deployments.set(result);
          if (this.requestedDeploymentId) {
            const deployment = result.find((deployment) => {
              return deployment.id === this.requestedDeploymentId;
            }) || null;
            this.currentDeployment.set(deployment);
            this.requestedDeploymentId = null;
          }
          // if (this.currentDeployment() === null && result.length > 0) {
          //   this.currentDeployment.set(result[0] || null);
          // }
        });
      } else {
        this.deployments.set([]);
      }
    });

    effect(() => {
      const currentDeployment = this.currentDeployment();
      if (currentDeployment === null) {
        this.dataCatalogs.set([]);
        return;
      }
      this.dataCatalogsForDeployment(currentDeployment).pipe(
        map((catalogs: DataCatalog[]) => {
          catalogs.forEach((catalog) => {
            catalog.deployment = currentDeployment;
          });
          return catalogs;
        })
      ).subscribe((catalogs: DataCatalog[]) => {
        console.log('DataCatalogs:', catalogs);
        this.dataCatalogs.set(catalogs);
        this.catalogDatasetCount.set({});
        catalogs.forEach((catalog) => {
          this.getDatasets(currentDeployment.id, catalog.id).subscribe((result) => {
            const total = result.total || 0;
            this.catalogDatasetCount.update((count) => {
              count[catalog.id] = total;
              return count;
            });
          });
        });
      });
    });
  }

  callApi(endpoint: string, params: any = {}): Observable<any> {
    return this.http.get(environment.adminEndpoint + endpoint, {
      headers: {
        Authorization: `Bearer ${(this.token())}`
      },
      params: params
    });
  }

  loadDeployments(): Observable<Deployment[]> {
    return this.callApi('deployments').pipe(
      map((response: any) => {
        return (response as Deployment[]) || [];
      })
    );
  }

  setDeploymentId(deploymentId: string | null): void {
    const deployments = this.deployments();
    if (deployments.length > 0) {
      const deployment = deployments.find((deployment) => {
        return deployment.id === deploymentId;
      }) || null;
      this.currentDeployment.set(deployment);
    } else {
      this.requestedDeploymentId = deploymentId;
    }
  }

  dataCatalogsForDeployment(deployment: Deployment): Observable<DataCatalog[]> {
    return this.callApi(`deployment/${deployment.id}/catalogs`).pipe(
      map((response: any) => {
        return (response as DataCatalog[]) || [];
      })
    );
  }

  getDatacatalog(deploymentId: string, catalogId: string): Observable<DataCatalog | null> {
    return this.callApi(`deployment/${deploymentId}/catalog/${catalogId}`).pipe(
      map((response: any) => {
        return (response as DataCatalog) || null;
      })
    );  
  }

  getDatasets(deploymentId: string, catalogId: string, page?: number, sort?: string): Observable<DatasetResult> {
    const params = {
      page: page || 1,
      sort: sort || '-last_updated',
    };
    return this.callApi(`deployment/${deploymentId}/catalog/${catalogId}/datasets`, params).pipe(
      map((response: any) => {
        const datasets = response.datasets as Dataset[];
        const total = response.total as number;
        const pages = response.pages as number;
        return { datasets, total, pages, page: page || 1 };
      })
    );
  }

  getDataset(deploymentId: string, catalogId: string, datasetId: string): Observable<Dataset | null> {
    return this.callApi(`deployment/${deploymentId}/catalog/${catalogId}/dataset/${datasetId}`).pipe(
      map((response: any) => {
        return (response as Dataset) || null;
      })
    );
  }
}
