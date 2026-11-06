import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-doctor-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="bar">
      <a class="brand" routerLink="/doctor">Pedia Centre · Doctor</a>
      @if (!auth.session()?.mustChangePassword) {
        <nav>
          <a routerLink="/doctor/schedule" routerLinkActive="active">My schedule</a>
          <a routerLink="/doctor/patients" routerLinkActive="active">My patients</a>
        </nav>
      } @else {
        <nav></nav>
      }
      @if (auth.session()?.name) {
        <span class="who">Dr. {{ auth.session()?.name }}</span>
      }
      <button type="button" class="logout" (click)="auth.logout()">Log out</button>
    </header>
    <main class="content">
      <router-outlet />
    </main>
  `,
  styles: `
    :host { display: block; min-height: 100vh; background: #f2f7fb; font-family: system-ui, sans-serif; }
    .bar { display: flex; align-items: center; gap: 1.5rem; padding: .75rem 1.5rem; background: #1d4f91; color: #fff; }
    .brand { font-weight: 700; font-size: 1.2rem; color: #fff; text-decoration: none; }
    nav { display: flex; gap: 1rem; flex: 1; }
    nav a { color: #d7e6f7; text-decoration: none; padding: .35rem .6rem; border-radius: 6px; }
    nav a.active, nav a:hover { background: rgb(255 255 255 / 18%); color: #fff; }
    .who { font-size: .9rem; }
    .logout { border: 1px solid rgb(255 255 255 / 60%); background: transparent; color: #fff; padding: .4rem .9rem; border-radius: 8px; cursor: pointer; }
    .content { max-width: 960px; margin: 0 auto; padding: 1.5rem 1rem; }
  `,
})
export class DoctorLayout {
  auth = inject(AuthService);
}