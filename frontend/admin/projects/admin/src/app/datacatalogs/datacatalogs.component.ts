import { Component, signal } from '@angular/core';
import { ApiService } from '../api.service';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { StateService } from '../state.service';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-datacatalogs',
  imports: [
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './datacatalogs.component.html',
  styleUrl: './datacatalogs.component.less'
})
export class DatacatalogsComponent {
  constructor(public api: ApiService, private route: ActivatedRoute, private state: StateService) {
    this.state.updateFromRoute(this.route.snapshot)
  }
}
