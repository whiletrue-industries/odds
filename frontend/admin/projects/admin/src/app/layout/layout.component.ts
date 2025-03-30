import { Component, signal } from '@angular/core';
import { HeaderComponent } from '../header/header.component';
import { RouterOutlet } from '@angular/router';
import { NavComponent } from '../nav/nav.component';
import { User } from '@angular/fire/auth';
import { AuthService } from '../auth.service';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-layout',
  imports: [
    HeaderComponent,
    NavComponent,
    RouterOutlet,
    MatSidenavModule,
    MatButtonModule
  ],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.less'
})
export class LayoutComponent {
  user = signal<User | null>(null);
  constructor(public auth: AuthService, private api: ApiService) {
    auth.user.subscribe(user => {
      this.user.set(user);
    });
  }
}
