import { Routes } from '@angular/router';
import { LoginComponent } from './pages/auth/login/login.component';
import { DashboardComponent as AdminDashboard } from './pages/admin/dashboard/dashboard.component';
import { UsersComponent } from './pages/admin/users/users.component';
import { InfractionsComponent } from './pages/admin/infractions/infractions.component';
import { StatsComponent } from './pages/admin/stats/stats.component';
import { CamerasComponent } from './pages/admin/cameras/cameras.component';
import { DashboardComponent as UserDashboard } from './pages/user/dashboard/dashboard.component';
import { MyInfractionsComponent } from './pages/user/my-infractions/my-infractions.component';
import { HistoryComponent } from './pages/user/history/history.component';
import { ProfileComponent } from './pages/user/profile/profile.component';
import { AuthGuard } from './guards/auth-guard';
import { AdminGuard } from './guards/admin.guard';
import { UserGuard } from './guards/user.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },

  // ADMIN
  { path: 'admin/dashboard', component: AdminDashboard, canActivate: [AuthGuard, AdminGuard] },
  { path: 'admin/users', component: UsersComponent, canActivate: [AuthGuard, AdminGuard] },
  { path: 'admin/infractions', component: InfractionsComponent, canActivate: [AuthGuard, AdminGuard] },
  { path: 'admin/stats', component: StatsComponent, canActivate: [AuthGuard, AdminGuard] },
  { path: 'admin/cameras', component: CamerasComponent, canActivate: [AuthGuard, AdminGuard] },

   { path: 'user/my-infractions', component: MyInfractionsComponent, canActivate: [AuthGuard, UserGuard] },
  { path: 'user/history', component: HistoryComponent, canActivate: [AuthGuard, UserGuard] },

  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' }
];
