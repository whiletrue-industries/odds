import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';

export const routes: Routes = [
    {
        path: 'a/:id', component: HomeComponent
    },
    {
        path: '', component: HomeComponent
    }
];
