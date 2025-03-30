import { Component } from '@angular/core';
import { Auth, AuthProvider, GoogleAuthProvider, signInWithPopup } from '@angular/fire/auth';
import { Router } from '@angular/router';
import {MatButtonModule} from '@angular/material/button'; 
import { filter, first, skip, take } from 'rxjs';
import { AuthService } from '../auth.service';
import { LayoutComponent } from '../layout/layout.component';

@Component({
  selector: 'app-login',
  imports: [
    MatButtonModule,
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.less'
})
export class LoginComponent {

  constructor(private afAuth: Auth, private auth: AuthService, private router: Router) {
  }
  
  loginGoogle() {
    this.login(new GoogleAuthProvider());
  }

  // loginEmail() {
  //   const email = (document.getElementById('email') as HTMLInputElement).value;
  //   const password = (document.getElementById('password') as HTMLInputElement).value;
  //   this.afAuth.signInWithEmailAndPassword(email, password);
  //   this.auth.user.pipe(filter((user) => !!user),take(1)).subscribe(user => {
  //     if (user) {
  //       // User is logged in - redirect to home
  //       this.router.navigate(['/']);
  //     }
  //   });
  // }

  login(provider: AuthProvider) {
    signInWithPopup(this.afAuth, provider);
    this.auth.user.pipe(filter((user) => !!user),take(1)).subscribe(user => {
      if (user) {
        // User is logged in - redirect to home
        this.router.navigate(['/']);
      }
    });
  }
}
