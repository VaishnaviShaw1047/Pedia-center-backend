import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { DoctorApi } from '../core/doctor-api.service';

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const a = group.get('new_password')?.value;
  const b = group.get('confirm_password')?.value;
  return a && b && a !== b ? { mismatch: true } : null;
}

@Component({
  selector: 'app-change-password',
  imports: [ReactiveFormsModule],
  template: `
    <section class="card">
      <h1>Change your password</h1>
      @if (auth.session()?.mustChangePassword) {
        <p class="notice">You are using a temporary password. Please set a new one to continue.</p>
      }

      <form [formGroup]="form" (ngSubmit)="submit()">
        <label>
          Current password
          <input type="password" formControlName="current_password" autocomplete="current-password" />
        </label>
        <label>
          New password (minimum 8 characters)
          <input type="password" formControlName="new_password" autocomplete="new-password" />
        </label>
        @if (form.controls.new_password.touched && form.controls.new_password.invalid) {
          <small class="err">Use at least 8 characters</small>
        }
        <label>
          Confirm new password
          <input type="password" formControlName="confirm_password" autocomplete="new-password" />
        </label>
        @if (form.hasError('mismatch') && form.controls.confirm_password.touched) {
          <small class="err">Passwords do not match</small>
        }

        @if (error()) {
          <p class="err">{{ error() }}</p>
        }

        <button class="primary" type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Saving…' : 'Update password' }}
        </button>
      </form>
    </section>
  `,
  styles: `
    .card { max-width: 420px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 16px; box-shadow: 0 8px 30px rgb(0 0 0 / 8%); }
    h1 { margin: 0 0 1rem; font-size: 1.4rem; color: #1d4f91; }
    .notice { padding: .6rem .8rem; background: #fff4d6; color: #8a5b00; border-radius: 8px; font-size: .9rem; }
    label { display: block; margin-top: .85rem; font-size: .9rem; }
    input { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #cfdcec; border-radius: 8px; }
    .primary { width: 100%; margin-top: 1.25rem; padding: .7rem; border: 0; border-radius: 8px; background: #1d4f91; color: #fff; cursor: pointer; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .err { display: block; color: #b3261e; font-size: .85rem; margin-top: .3rem; }
  `,
})
export class ChangePassword {
  private fb = inject(NonNullableFormBuilder);
  private api = inject(DoctorApi);
  private router = inject(Router);
  auth = inject(AuthService);

  loading = signal(false);
  error = signal<string | null>(null);

  form = this.fb.group(
    {
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );

  submit() {
    if (this.form.invalid) return;
    const { current_password, new_password } = this.form.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    this.api.changePassword(current_password, new_password).subscribe({
      next: () => {
        this.auth.markPasswordChanged();
        this.router.navigate(['/doctor']);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(
          typeof e.error?.detail === 'string' ? e.error.detail : 'Could not update the password.',
        );
      },
    });
  }
}