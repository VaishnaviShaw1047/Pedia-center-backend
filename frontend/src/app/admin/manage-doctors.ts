import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AdminApi } from '../core/admin-api.service';
import { errorMessage } from '../core/error-message';
import { DoctorSummary } from '../core/models';

@Component({
  selector: 'app-manage-doctors',
  imports: [RouterLink],
  template: `
    <div class="head">
      <h1>Doctors</h1>
      <a class="primary" routerLink="/admin/doctors/new">+ Add doctor</a>
    </div>

    <div class="searchbar">
      <input #q type="search" placeholder="Search by name or specialty" (keyup.enter)="load(q.value)" />
      <button type="button" class="secondary" (click)="load(q.value)">Search</button>
    </div>

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading…</p>
    } @else {
      <p class="muted">{{ doctors().length }} doctor(s)</p>
      <div class="list">
        @for (d of doctors(); track d.doctor_id) {
          <article class="card">
            <div class="info">
              <h2>Dr. {{ d.first_name }} {{ d.last_name }} <span class="muted">({{ d.staff_id }})</span></h2>
              <p class="sub">{{ d.specialty }} · {{ d.qualification }}</p>
              <p>{{ d.experience_years }} years · ₹{{ d.consultation_fee }}</p>
              @if (d.languages) { <p class="muted">Languages: {{ d.languages }}</p> }
              @if (d.available_days) { <p class="muted">Days: {{ d.available_days }}</p> }
            </div>
            <a class="secondary" [routerLink]="['/admin/doctors', d.doctor_id, 'availability']">
              Set availability
            </a>
          </article>
        } @empty {
          <div class="card"><p class="muted">No doctors found.</p></div>
        }
      </div>
    }
  `,
  styles: `
    .head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    h1 { margin: 0; color: #4b3a8a; }
    .searchbar { display: flex; gap: .5rem; margin-bottom: .75rem; }
    .searchbar input { flex: 1; padding: .6rem; border: 1px solid #d6d0ea; border-radius: 8px; }
    .primary { padding: .5rem 1rem; border-radius: 8px; background: #4b3a8a; color: #fff; text-decoration: none; }
    .secondary { padding: .5rem 1rem; border: 1px solid #4b3a8a; background: #fff; color: #4b3a8a; border-radius: 8px; text-decoration: none; cursor: pointer; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .card h2 { margin: 0; font-size: 1.05rem; }
    .card p { margin: .2rem 0; font-size: .9rem; }
    .sub { color: #4b3a8a; font-weight: 600; }
    .muted { color: #6b6785; }
    .err { color: #b3261e; }
    @media (max-width: 600px) { .card { flex-direction: column; align-items: flex-start; } }
  `,
})
export class ManageDoctors implements OnInit {
  private api = inject(AdminApi);

  doctors = signal<DoctorSummary[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);

  ngOnInit() {
    this.load('');
  }

  load(search: string) {
    this.loading.set(true);
    this.error.set(null);
    this.api.doctors(search).subscribe({
      next: (rows) => {
        this.doctors.set(rows);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(errorMessage(e, 'Could not load doctors.'));
      },
    });
  }
}