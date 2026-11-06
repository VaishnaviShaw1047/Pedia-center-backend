import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DoctorApi } from '../core/doctor-api.service';
import { PatientSummary } from '../core/models';

@Component({
  selector: 'app-my-patients',
  imports: [DatePipe, RouterLink],
  template: `
    <h1>My patients</h1>

    <input
      class="search"
      type="search"
      placeholder="Search by name, MRN or guardian mobile"
      [value]="query()"
      (input)="query.set($any($event.target).value)"
    />

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading…</p>
    } @else {
      <p class="muted">{{ filtered().length }} patient(s)</p>
      <div class="list">
        @for (p of filtered(); track p.patient_id) {
          <article class="card">
            <div class="info">
              <h2>{{ p.first_name }} {{ p.last_name }} <span class="muted">({{ p.mrn }})</span></h2>
              <p>
                {{ p.gender }} · Born {{ p.date_of_birth | date: 'd MMM y' }}
                @if (p.blood_group) { · {{ p.blood_group }} }
              </p>
              <p class="muted">Guardian: {{ p.guardian_name }} · {{ p.guardian_mobile }}</p>
            </div>
            <div class="row">
              <a class="secondary" [routerLink]="['/doctor/patients', p.patient_id]">History</a>
              <a class="primary" [routerLink]="['/doctor/patients', p.patient_id, 'add-record']">Add record</a>
            </div>
          </article>
        } @empty {
          <div class="card"><p class="muted">No patients found.</p></div>
        }
      </div>
    }
  `,
  styles: `
    h1 { margin: 0 0 1rem; color: #1d4f91; }
    .search { width: 100%; box-sizing: border-box; padding: .65rem; border: 1px solid #cfdcec; border-radius: 8px; margin-bottom: .5rem; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .info h2 { margin: 0; font-size: 1.05rem; }
    .info p { margin: .2rem 0; font-size: .9rem; }
    .row { display: flex; gap: .5rem; flex-wrap: wrap; }
    .primary { padding: .4rem .9rem; border-radius: 8px; background: #1d4f91; color: #fff; text-decoration: none; font-size: .9rem; }
    .secondary { padding: .4rem .9rem; border: 1px solid #1d4f91; border-radius: 8px; color: #1d4f91; text-decoration: none; font-size: .9rem; }
    .muted { color: #5b7480; }
    .err { color: #b3261e; }
    @media (max-width: 600px) { .card { flex-direction: column; align-items: flex-start; } }
  `,
})
export class MyPatients implements OnInit {
  private api = inject(DoctorApi);

  patients = signal<PatientSummary[]>([]);
  query = signal('');
  loading = signal(true);
  error = signal<string | null>(null);

  filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.patients();
    return this.patients().filter((p) =>
      [p.first_name, p.last_name, p.mrn, p.guardian_name, p.guardian_mobile]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q)),
    );
  });

  ngOnInit() {
    this.api.patients().subscribe({
      next: (rows) => {
        this.patients.set(rows);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(
          typeof e.error?.detail === 'string' ? e.error.detail : 'Could not load your patients.',
        );
      },
    });
  }
}