import { Routes } from '@angular/router';
import { MainComponent } from './main/main.component';
import { AppComponent } from './app.component';
import { AuthGuard } from './auth.guard';
import { LoginComponent } from './login/login.component';
import { DatasetsComponent } from './datasets/datasets.component';
import { WebsitesComponent } from './websites/websites.component';
import { DatacatalogsComponent } from './datacatalogs/datacatalogs.component';
import { DatasetComponent } from './dataset/dataset.component';
import { ResourceComponent } from './resource/resource.component';

export const routes: Routes = [
    {
        path: 'login',
        component: LoginComponent,        
    },
    {
        path: 'deployment/:deploymentId/websites',
        component: WebsitesComponent,
        canActivate: [AuthGuard],
    },
    {
        path: 'deployment/:deploymentId/catalog/:catalogId/dataset/:datasetId/:resourceIdx',
        component: ResourceComponent,
        canActivate: [AuthGuard],
    },
    {
        path: 'deployment/:deploymentId/catalog/:catalogId/dataset/:datasetId',
        component: DatasetComponent,
        canActivate: [AuthGuard],
    },
    {
        path: 'deployment/:deploymentId/catalog/:catalogId/datasets',
        component: DatasetsComponent,
        canActivate: [AuthGuard],
    },
    {
        path: 'deployment/:deploymentId/catalogs',
        component: DatacatalogsComponent,
        canActivate: [AuthGuard],
    },
    {
        path: 'deployment/:deploymentId',
        component: MainComponent,
        canActivate: [AuthGuard],
    },
    {
        path: '',
        component: MainComponent,
        canActivate: [AuthGuard],
    },

];
