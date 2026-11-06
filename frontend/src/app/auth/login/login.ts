import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router , RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { Role } from '../../core/models';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <main class="card">
      <h1>Pedia Centre</h1>

      <div class="tabs">
        @for (m of modes; track m.value) {
          <button type="button" [class.active]="mode() === m.value" (click)="setMode(m.value)">
            {{ m.label }}
          </button>
        }
      </div>

      <form [formGroup]="form" (ngSubmit)="submit()">
        <label>
          {{ identifierLabel[mode()] }}
          <input formControlName="identifier" autocomplete="username" />
        </label>
        @if (form.controls.identifier.touched && form.controls.identifier.invalid) {
          <small class="err">
            {{ mode() === 'guardian' ? 'Enter a valid 10-digit mobile number' : 'This field is required' }}
          </small>
        }

        <label>
          Password
          <input type="password" formControlName="password" autocomplete="current-password" />
        </label>

        @if (error()) {
          <p class="err">{{ error() }}</p>
        }

        <button class="primary" type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Signing in…' : 'Sign in' }}
        </button>
              @if (mode() === 'guardian') {
        <p class="foot">New parent? <a routerLink="/register">Create an account</a></p>
      }
      </form>
    </main>
  `,
  styles: `
    :host { display: grid; min-height: 100vh; place-items: center; background: #f2f7fb; font-family: system-ui, sans-serif; }
    .card { width: min(380px, 92vw); padding: 2rem; background: #fff; border-radius: 16px; box-shadow: 0 8px 30px rgb(0 0 0 / 8%); }
    h1 { margin: 0 0 1rem; font-size: 1.5rem; color: #0b6e8a; }
    .tabs { display: flex; gap: .5rem; margin-bottom: 1rem; }
    .tabs button { flex: 1; padding: .5rem; border: 1px solid #cfe3ec; background: #fff; border-radius: 8px; cursor: pointer; }
    .tabs button.active { background: #0b6e8a; color: #fff; border-color: #0b6e8a; }
    label { display: block; margin-top: .75rem; font-size: .9rem; }
    input { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #cfe3ec; border-radius: 8px; }
    .primary { width: 100%; margin-top: 1.25rem; padding: .7rem; border: 0; border-radius: 8px; background: #0b6e8a; color: #fff; cursor: pointer; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .err { color: #b3261e; font-size: .85rem; }
    .foot { text-align: center; font-size: .9rem; margin-top: 1rem; }
  `,
})
export class Login {
  private fb = inject(NonNullableFormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);

  modes: { value: Role; label: string }[] = [
    { value: 'guardian', label: 'Parent' },
    { value: 'doctor', label: 'Doctor' },
    { value: 'admin', label: 'Admin' },
  ];
  identifierLabel: Record<Role, string> = {
    guardian: 'Mobile number',
    doctor: 'Staff ID',
    admin: 'Username',
  };

  mode = signal<Role>('guardian');
  loading = signal(false);
  error = signal<string | null>(null);

  form = this.fb.group({
    identifier: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
    password: ['', Validators.required],
  });

  setMode(mode: Role) {
    this.mode.set(mode);
    this.error.set(null);
    const ctrl = this.form.controls.identifier;
    ctrl.setValidators(
      mode === 'guardian'
        ? [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]
        : [Validators.required],
    );
    ctrl.updateValueAndValidity();
  }

  submit() {
    if (this.form.invalid) return;
    const { identifier, password } = this.form.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    const request$ =
      this.mode() === 'guardian'
        ? this.auth.loginGuardian(identifier, password)
        : this.mode() === 'doctor'
          ? this.auth.loginDoctor(identifier, password)
          : this.auth.loginAdmin(identifier, password);

    request$.subscribe({
      next: (session) => this.router.navigate(['/', session.role]),
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        const detail = err.error?.detail;
        this.error.set(typeof detail === 'string' ? detail : 'Login failed. Please try again.');
      },
    });
    
  }
}