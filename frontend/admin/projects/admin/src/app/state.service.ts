import { effect, Injectable, signal } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import { Subscription } from 'rxjs';
import { DataCatalog, Dataset } from './datatypes';
import { ApiService } from './api.service';
import { Sort } from '@angular/material/sort';

@Injectable({
  providedIn: 'root'
})
export class StateService {

  deploymentId = signal<string | null>(null);
  catalogId = signal<string | null>(null);
  datasetId = signal<string | null>(null);
  resourceIndex = signal<number | null>(null);
  catalog = signal<DataCatalog | null>(null);
  dataset = signal<Dataset | null>(null);
  currentPage = signal<number>(1);

  defaultSort = '-last_updated';
  currentSort = signal<Sort | null>(null);
  currentSortDirective = signal<string>(this.defaultSort);

  constructor(private api: ApiService) {
    effect(() => {
      const deploymentId = this.deploymentId();
      const catalogId = this.catalogId();
      if (catalogId && deploymentId) {
        this.api.getDatacatalog(deploymentId, catalogId).subscribe((catalog) => {
          this.catalog.set(catalog);
        });
        this.currentPage.set(1);
      } else {
        this.catalog.set(null);
      }
    });
    effect(() => {
      const deploymentId = this.deploymentId();
      const catalogId = this.catalogId();
      const datasetId = this.datasetId(); 
      if (datasetId && catalogId && deploymentId) {
        this.api.getDataset(deploymentId, catalogId, datasetId).subscribe((dataset) => {
          this.dataset.set(dataset);
        });
      } else {
        this.dataset.set(null);
      }
    });
  }

  updateFromRoute(route: ActivatedRouteSnapshot) {
    this.deploymentId.set(route.params['deploymentId'] || null);
    this.api.setDeploymentId(this.deploymentId());
    this.catalogId.set(route.params['catalogId'] || null);
    this.datasetId.set(route.params['datasetId'] || null);
    const resourceIdx = parseInt(route.params['resourceIdx']);
    if (resourceIdx >= 0) {
      this.resourceIndex.set(resourceIdx);
    } else {
      this.resourceIndex.set(null);
    }
  }
}
