import { Component, Input, signal, WritableSignal } from '@angular/core';
import { AuthService } from '../auth.service';
import { User } from '@angular/fire/auth';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { ApiService } from '../api.service';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Deployment } from '../datatypes';

@Component({
  selector: 'app-header',
  imports: [
    FormsModule,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MatMenuModule,
    MatButtonModule,
    MatDividerModule,
    MatSelectModule,
    MatFormFieldModule,
  ],
  templateUrl: './header.component.html',
  styleUrl: './header.component.less'
})
export class HeaderComponent {
  @Input() user: WritableSignal<User | null>;
  constructor(public auth: AuthService, public api: ApiService, private router: Router) {}

  changeDeployment(deployment: Deployment) {
    this.router.navigate(['/deployment', deployment.id]);
  }
}
