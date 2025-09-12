import { Routes } from '@angular/router';
import { CategoryComponent } from './pages/category/category.component';
import { HomeComponent } from './pages/home/home.component';
import { SingleComponent } from './pages/single/single.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'category', component: CategoryComponent },
  { path: 'single/:id', component: SingleComponent },
  { path: '**', redirectTo: '' },
];
