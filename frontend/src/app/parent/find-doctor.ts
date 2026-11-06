import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DoctorPublic, SpecialtyCount } from '../core/models';
import { ParentApi } from '../core/parent-api.service';

@Component({
 selector: 'app-find-doctor',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <h1>Find a doctor</h1>

    <form class="filters" [formGroup]="filters" (ngSubmit)="search()">
      <label>
        Specialty
        <select formControlName="specialty">
          <option value="">All specialties</option>
          @for (s of specialties(); track s.specialty) {
            <option [value]="s.specialty">{{ s.specialty }} ({{ s.doctor_count }})</option>
          }
        </select>
      </label>

      <label>
        Language
        <input formControlName="language" placeholder="e.g. Bengali" />
      </label>

      <label>
        Max fee (₹)
        <input type="number" min="0" formControlName="max_fee" placeholder="Any" />
      </label>

      <label>
        Day
        <select formControlName="day">
          <option value="">Any day</option>
          @for (d of days; track d) {
            <option [value]="d">{{ d }}</option>
          }
        </select>
      </label>

      <div class="actions">
        <button type="submit" class="primary" [disabled]="loading()">Search</button>
        <button type="button" class="secondary" (click)="reset()">Reset</button>
      </div>
    </form>

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading doctors…</p>
    } @else {
      <p class="muted">{{ doctors().length }} doctor(s) found</p>

      <div class="list">
        @for (d of doctors(); track d.doctor_id) {
          <article class="card">
            <div class="info">
              <h2>Dr. {{ d.first_name }} {{ d.last_name }}</h2>
              <p class="sub">{{ d.specialty }} · {{ d.qualification }}</p>
              <p>{{ d.experience_years }} years of experience</p>
              @if (d.languages) {
                <p>Languages: {{ d.languages }}</p>
              }
              @if (d.available_days) {
                <p>Available: {{ d.available_days }}</p>
              }
            </div>
            <div class="side">
              <div class="fee">₹{{ d.consultation_fee }}</div>
              <a class="primary" [routerLink]="['/guardian/book', d.doctor_id]">Book appointment</a>
            </div>
          </article>
        } @empty {
          <p class="muted">No doctors match these filters.</p>
        }
      </div>
    }
  `,
  styles: `
    h1 { margin: 0 0 1rem; color: #0b6e8a; }
    .filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .75rem 1rem; align-items: end; padding: 1rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    label { display: block; font-size: .85rem; }
    input, select { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .55rem; border: 1px solid #cfe3ec; border-radius: 8px; background: #fff; }
    .actions { display: flex; gap: .5rem; }
    .primary { display: inline-block; padding: .55rem 1rem; border: 0; border-radius: 8px; background: #0b6e8a; color: #fff; text-decoration: none; cursor: pointer; font-size: .9rem; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .secondary { padding: .55rem 1rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 8px; cursor: pointer; }
    .muted { color: #5b7480; font-size: .9rem; }
    .err { color: #b3261e; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; justify-content: space-between; gap: 1rem; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .card h2 { margin: 0; font-size: 1.1rem; }
    .card p { margin: .2rem 0; font-size: .9rem; }
    .sub { color: #0b6e8a; font-weight: 600; }
    .side { display: flex; flex-direction: column; align-items: flex-end; justify-content: space-between; gap: .5rem; }
    .fee { font-size: 1.3rem; font-weight: 700; }
    @media (max-width: 560px) { .card { flex-direction: column; } .side { align-items: flex-start; } }
  `,
})
export class FindDoctors implements OnInit {
  private api = inject(ParentApi);
  private fb = inject(NonNullableFormBuilder);

  days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  specialties = signal<SpecialtyCount[]>([]);
  doctors = signal<DoctorPublic[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  filters = this.fb.group({
    specialty: '',
    language: '',
    max_fee: '',
    day: '',
  });

  ngOnInit() {
    this.api.specialties().subscribe({
      next: (rows) => this.specialties.set(rows),
      error: () => {}, // the filter still works without the dropdown counts
    });
    this.search();
  }

  search() {
    const f = this.filters.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    this.api
      .doctors({
        specialty: f.specialty,
        language: f.language,
        day: f.day,
        max_fee: f.max_fee === '' ? null : Number(f.max_fee),
      })
      .subscribe({
        next: (rows) => {
          this.doctors.set(rows);
          this.loading.set(false);
        },
        error: (err: HttpErrorResponse) => {
          this.loading.set(false);
          this.error.set(
            typeof err.error?.detail === 'string'
              ? err.error.detail
              : 'Could not load doctors. Is the backend running?',
          );
        },
      });
  }

  reset() {
    this.filters.reset();
    this.search();
  }
}