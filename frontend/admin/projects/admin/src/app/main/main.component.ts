import { Component } from '@angular/core';
import { LayoutComponent } from "../layout/layout.component";
import { ApiService } from '../api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { StateService } from '../state.service';
import { DataCatalog } from '../datatypes';
import { toObservable } from '@angular/core/rxjs-interop';
import { first } from 'rxjs';

@Component({
  selector: 'app-main',
  imports: [],
  templateUrl: './main.component.html',
  styleUrl: './main.component.less'
})
export class MainComponent {
  constructor(private api: ApiService, private route: ActivatedRoute, private state: StateService, private router: Router) {
    toObservable(this.api.token).pipe(
      first(),
    ).subscribe(token => {
      this.state.updateFromRoute(this.route.snapshot);
      const deploymentId = this.state.deploymentId();
      console.log('MAIN DEP ID', token, deploymentId);
      if (!deploymentId) {
        this.api.loadDeployments().subscribe(deployments => {
          if (deployments.length > 0) {
            console.log('MAIN 1st DEP ID', deployments[0].id);
            this.router.navigate(['/deployment', deployments[0].id]);
          }
        });
      } else {
        this.api.dataCatalogsForDeployment(deploymentId).subscribe(catalogs => {
          if (catalogs.length > 0) {
            console.log('MAIN 1st CAT KIND', catalogs[0].kind);
            const catalog: DataCatalog = catalogs[0];
            if (catalog.kind === 'website') {
              this.router.navigate(['/deployment', deploymentId, 'websites']);
            } else {
              this.router.navigate(['/deployment', deploymentId, 'catalogs']);
            }
          }
        });
      }
    });
  }

}
