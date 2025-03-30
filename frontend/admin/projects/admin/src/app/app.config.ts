import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { getApp, initializeApp, provideFirebaseApp } from '@angular/fire/app';
import { getAuth, provideAuth } from '@angular/fire/auth';
import { getFirestore, provideFirestore } from '@angular/fire/firestore';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';


const firebaseConfig = {
  apiKey: "AIzaSyBhHdaKQw9rNZhwPZCjWRWE1MpDt0utDPQ",
  authDomain: "oddsadmin.firebaseapp.com",
  projectId: "oddsadmin",
  storageBucket: "oddsadmin.firebasestorage.app",
  messagingSenderId: "1026312462623",
  appId: "1:1026312462623:web:39927d973520afcd5bd02a",
  measurementId: "G-36LMNGTHSK"
};


export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideFirebaseApp(() => initializeApp(firebaseConfig)),
    provideClientHydration(withEventReplay()),
    provideAuth(() => getAuth(getApp())),
    provideFirestore(() => getFirestore()), 
  ]
};
