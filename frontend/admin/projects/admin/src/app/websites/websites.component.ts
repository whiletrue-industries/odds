import { Component } from '@angular/core';
import { ApiService } from '../api.service';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { StateService } from '../state.service';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-websites',
  imports: [
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './websites.component.html',
  styleUrl: './websites.component.less'
})
export class WebsitesComponent {
  constructor(public api: ApiService, private route: ActivatedRoute, private state: StateService) {
    this.state.updateFromRoute(this.route.snapshot)
  }
}
