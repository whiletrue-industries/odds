import { Component, computed } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterLink } from '@angular/router';
import { ApiService } from '../api.service';
import { StateService } from '../state.service';

@Component({
  selector: 'app-nav',
  imports: [
    MatListModule,
    MatIconModule,
    RouterLink,
  ],
  templateUrl: './nav.component.html',
  styleUrl: './nav.component.less'
})

// <mat-list-item [activated]="true" [routerLink]="['/websites']">
// <mat-icon matListItemIcon>language</mat-icon>
// <span matListItemTitle>My Websites</span>
// </mat-list-item>
// <mat-list-item [activated]="false" [routerLink]="['/datacatalogs']">
// <mat-icon matListItemIcon>inventory_2</mat-icon>
// <span matListItemTitle>My Data Catalogs</span>
// </mat-list-item>
// <mat-list-item [activated]="false" [routerLink]="['/datasets']">
// <mat-icon matListItemIcon>dataset</mat-icon>
// <span matListItemTitle>Datasets</span>
// </mat-list-item>

export class NavComponent {
  navItems = computed<any[]>(() => {
    const deployment = this.api.currentDeployment();
    const deploymentId = deployment ? deployment.id : '_';
    const numWebsites = this.api.websites().length;
    const numCatalogs = this.api.catalogs().length;
    const ret = [];
    if (numWebsites > 0) {
      ret.push({
        title: 'My Websites',
        icon: 'language',
        route: `/deployment/${deploymentId}/websites`
      });
    }
    if (numCatalogs > 0) {
      ret.push({
        title: 'My Data Catalogs',
        icon: 'inventory_2',
        route: `/deployment/${deploymentId}/catalogs`
      });
    }
    ret.push({
      title: 'Questions',
      icon: 'contact_support',
      route: `/deployment/${deploymentId}/questions`
    });
    return ret;
  });

  constructor(public api: ApiService, private state: StateService) {
  }

  isActive(route: string): boolean {
    return window.location.pathname.indexOf(route) === 0;
  }
}
