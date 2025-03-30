import { Component } from '@angular/core';
import { LayoutComponent } from "../layout/layout.component";
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import { StateService } from '../state.service';

@Component({
  selector: 'app-main',
  imports: [],
  templateUrl: './main.component.html',
  styleUrl: './main.component.less'
})
export class MainComponent {
  constructor(private api: ApiService, private route: ActivatedRoute, private state: StateService) {
    this.state.updateFromRoute(this.route.snapshot);
  }

}
