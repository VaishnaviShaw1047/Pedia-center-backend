import { Component, inject } from '@angular/core';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-home',
  template: `
    <main style="padding: 2rem; font-family: system-ui, sans-serif">
      <h1>Welcome{{ auth.session()?.name ? ', ' + auth.session()?.name : '' }}</h1>
      <p>Signed in as <strong>{{ auth.role() }}</strong> (id {{ auth.session()?.userId }})</p>
      <button (click)="auth.logout()">Log out</button>
    </main>
  `,
})
export class Home {
  auth = inject(AuthService);
}