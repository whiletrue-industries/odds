import { Injectable } from '@angular/core';
import { Auth, User } from '@angular/fire/auth';
import { Router } from '@angular/router';
import { ReplaySubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  user = new ReplaySubject<User | null>(1);

  constructor(private afAuth: Auth, private router: Router) {
    this.afAuth.onAuthStateChanged(user => {
      this.user.next(user);
    });
  }

  logout() {
    this.afAuth.signOut();
    this.router.navigate(['/login']);
  }
}
