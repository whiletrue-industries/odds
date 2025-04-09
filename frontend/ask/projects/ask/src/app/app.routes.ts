import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { MobileComponent } from './mobile/mobile.component';

export const routes: Routes = [
    {
        path: 'm/:deployment/a/:id', component: MobileComponent
    },
    {
        path: 'm/:deployment', component: MobileComponent
    },
    {
        path: ':deployment/a/:id', component: HomeComponent
    },
    {
        path: ':deployment', component: HomeComponent
    }
];
