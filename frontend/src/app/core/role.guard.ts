import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Role } from './models';

export const roleGuard =
  (role: Role): CanActivateFn =>
  () => {
    const auth = inject(AuthService);
    const router = inject(Router);
    return auth.role() === role ? true : router.createUrlTree(['/login']);
  };
  export const passwordChangedGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.session()?.mustChangePassword
    ? router.createUrlTree(['/doctor/change-password'])
    : true;
};