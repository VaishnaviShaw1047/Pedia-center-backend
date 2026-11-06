import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AdminApi } from '../core/admin-api.service';
import { errorMessage } from '../core/error-message';
import { DoctorCreateResponse } from '../core/models';

interface Field {
  key: string;
  label: string;
  type?: string;
}

@Component({
  selector: 'app-add-doctor',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <a class="back" routerLink="/admin/doctors">← Back to doctors</a>

    @if (created(); as c) {
      <section class="card">
        <h1>Doctor created</h1>
        <p>Dr. {{ c.first_name }} {{ c.last_name }} ({{ c.specialty }})</p>
        <p>Staff ID: <strong>{{ c.staff_id }}</strong></p>
        <p class="muted">
          Share the staff ID and the temporary password with the doctor. They will be asked to change it on first login.
        </p>
        <div class="row">
          <a class="primary" [routerLink]="['/admin/doctors', c.doctor_id, 'availability']">Set availability</a>
          <button type="button" class="secondary" (click)="created.set(null)">Add another</button>
        </div>
      </section>
    } @else {
      <h1>Add a doctor</h1>
      <form class="card" [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <div class="grid">
          @for (f of fields; track f.key) {
            <label>
              {{ f.label }}
              <input [type]="f.type ?? 'text'" [formControlName]="f.key" />
              @if (form.get(f.key)?.touched && form.get(f.key)?.invalid) {
                <small class="err">Invalid or missing value</small>
              }
            </label>
          }
        </div>

        @if (error()) {
          <p class="err">{{ error() }}</p>
        }

        <button class="primary wide" type="submit" [disabled]="saving()">
          {{ saving() ? 'Creating…' : 'Create doctor' }}
        </button>
      </form>
    }
  `,
  styles: `
    .back { display: inline-block; margin-bottom: .75rem; color: #4b3a8a; text-decoration: none; }
    h1 { margin: 0 0 1rem; color: #4b3a8a; }
    .card { padding: 1.5rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .85rem 1rem; }
    label { display: block; font-size: .9rem; }
    input { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #d6d0ea; border-radius: 8px; }
    .primary { display: inline-block; padding: .65rem 1.2rem; border: 0; border-radius: 8px; background: #4b3a8a; color: #fff; text-decoration: none; cursor: pointer; text-align: center; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .wide { width: 100%; box-sizing: border-box; margin-top: 1.25rem; }
    .secondary { padding: .65rem 1.2rem; border: 1px solid #4b3a8a; background: #fff; color: #4b3a8a; border-radius: 8px; cursor: pointer; }
    .row { display: flex; gap: .75rem; margin-top: 1rem; flex-wrap: wrap; }
    .muted { color: #6b6785; }
    .err { color: #b3261e; font-size: .85rem; }
  `,
})
export class AddDoctor {
  private fb = inject(NonNullableFormBuilder);
  private api = inject(AdminApi);

  saving = signal(false);
  error = signal<string | null>(null);
  created = signal<DoctorCreateResponse | null>(null);

  fields: Field[] = [
    { key: 'first_name', label: 'First name' },
    { key: 'last_name', label: 'Last name' },
    { key: 'registration_no', label: 'Registration number' },
    { key: 'qualification', label: 'Qualification (e.g. MBBS, MD)' },
    { key: 'specialty', label: 'Specialty' },
    { key: 'experience_years', label: 'Experience (years)', type: 'number' },
    { key: 'consultation_fee', label: 'Consultation fee (₹)', type: 'number' },
    { key: 'languages', label: 'Languages (optional)' },
    { key: 'available_days', label: 'Available days (optional, e.g. Mon,Tue,Wed)' },
    { key: 'mobile_number', label: 'Mobile number (optional)', type: 'tel' },
    { key: 'email', label: 'Email (optional)', type: 'email' },
    { key: 'temporary_password', label: 'Temporary password (minimum 8 characters)' },
  ];

  form = this.fb.group({
    first_name: ['', [Validators.required, Validators.maxLength(50)]],
    last_name: ['', [Validators.required, Validators.maxLength(50)]],
    registration_no: ['', [Validators.required, Validators.maxLength(30)]],
    qualification: ['', [Validators.required, Validators.maxLength(150)]],
    specialty: ['', [Validators.required, Validators.maxLength(60)]],
    experience_years: [0, [Validators.required, Validators.min(0), Validators.max(70)]],
    consultation_fee: [0, [Validators.required, Validators.min(0)]],
    languages: ['', Validators.maxLength(100)],
    available_days: ['', Validators.maxLength(60)],
    mobile_number: ['', Validators.pattern(/^[6-9]\d{9}$/)],
    email: ['', Validators.email],
    temporary_password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error.set('Please fix the highlighted fields.');
      return;
    }

    const v = this.form.getRawValue();
    const orNull = (s: string) => (s && s.trim() ? s.trim() : null);

    this.saving.set(true);
    this.error.set(null);

    this.api
      .createDoctor({
        first_name: v.first_name.trim(),
        last_name: v.last_name.trim(),
        registration_no: v.registration_no.trim(),
        qualification: v.qualification.trim(),
        specialty: v.specialty.trim(),
        experience_years: Number(v.experience_years),
        consultation_fee: Number(v.consultation_fee),
        languages: orNull(v.languages),
        available_days: orNull(v.available_days),
        mobile_number: orNull(v.mobile_number),
        email: orNull(v.email),
        temporary_password: v.temporary_password,
      })
      .subscribe({
        next: (res) => {
          this.saving.set(false);
          this.created.set(res);
          this.form.reset();
        },
        error: (e: HttpErrorResponse) => {
          this.saving.set(false);
          this.error.set(errorMessage(e, 'Could not create the doctor.'));
        },
      });
  }
}