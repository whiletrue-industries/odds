import { effect, Injectable, signal } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import { Subscription } from 'rxjs';
import { DataCatalog, Dataset } from './datatypes';
import { ApiService } from './api.service';
import { Sort } from '@angular/material/sort';

export class PageState {
  currentPage = signal<number>(1);
  currentSort = signal<Sort | null>(null);
  currentSortDirective = signal<string | null>(null);
  textFilter = signal<string | null>(null);
}

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

  datasetsPage = new PageState();
  questionsPage = new PageState();
  webpagesPage = new PageState();
  pages = [this.datasetsPage, this.questionsPage, this.webpagesPage];

  constructor(private api: ApiService) {
    effect(() => {
      const deploymentId = this.deploymentId();
      const catalogId = this.catalogId();
      if (catalogId && deploymentId) {
        this.api.getDatacatalog(deploymentId, catalogId).subscribe((catalog) => {
          this.catalog.set(catalog);
        });
        this.pages.forEach((page) => {
          page.currentPage.set(1);
        });
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
