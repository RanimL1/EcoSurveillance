import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const AdminGuard: CanActivateFn = () => {
  const router = inject(Router);
  const role = localStorage.getItem('role');
  if (role === 'ADMIN') return true;
  router.navigate(['/user/my-infractions']);
  return false;
};
