import { Component } from '@angular/core';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import { StateService } from '../state.service';

@Component({
  selector: 'app-websites',
  imports: [],
  templateUrl: './websites.component.html',
  styleUrl: './websites.component.less'
})
export class WebsitesComponent {
  constructor(public api: ApiService, private route: ActivatedRoute, private state: StateService) {
    this.state.updateFromRoute(this.route.snapshot);
  }
}
