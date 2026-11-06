import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-parent-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="bar">
      <a class="brand" routerLink="/guardian">Pedia Centre</a>
      <nav>
        <a routerLink="/guardian/find-doctor" routerLinkActive="active">Find a doctor</a>
        <a routerLink="/guardian/appointments" routerLinkActive="active">My appointments</a>
      </nav>
      <button type="button" class="logout" (click)="auth.logout()">Log out</button>
    </header>
    <main class="content">
      <router-outlet />
    </main>
  `,
  styles: `
    :host { display: block; min-height: 100vh; background: #f2f7fb; font-family: system-ui, sans-serif; }
    .bar { display: flex; align-items: center; gap: 1.5rem; padding: .75rem 1.5rem; background: #0b6e8a; color: #fff; }
    .brand { font-weight: 700; font-size: 1.2rem; color: #fff; text-decoration: none; }
    nav { display: flex; gap: 1rem; flex: 1; }
    nav a { color: #d7eef5; text-decoration: none; padding: .35rem .6rem; border-radius: 6px; }
    nav a.active, nav a:hover { background: rgb(255 255 255 / 18%); color: #fff; }
    .logout { border: 1px solid rgb(255 255 255 / 60%); background: transparent; color: #fff; padding: .4rem .9rem; border-radius: 8px; cursor: pointer; }
    .content { max-width: 960px; margin: 0 auto; padding: 1.5rem 1rem; }
  `,
})
export class ParentLayout {
  auth = inject(AuthService);
}