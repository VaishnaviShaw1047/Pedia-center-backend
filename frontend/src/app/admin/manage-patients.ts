import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { AdminApi } from '../core/admin-api.service';
import { errorMessage } from '../core/error-message';
import { DoctorSummary, PatientSummary } from '../core/models';

@Component({
  selector: 'app-manage-patients',
  imports: [DatePipe],
  template: `
    <h1>Patients</h1>

    <div class="searchbar">
      <input #q type="search" placeholder="Search by name, MRN or guardian mobile" (keyup.enter)="search(q.value)" />
      <button type="button" class="secondary" (click)="search(q.value)">Search</button>
    </div>

    @if (error()) { <p class="err">{{ error() }}</p> }
    @if (message()) { <p class="ok">{{ message() }}</p> }

    @if (loading()) {
      <p class="muted">Loading…</p>
    } @else {
      <p class="muted">{{ total() }} patient(s) · page {{ page() }} of {{ totalPages() }}</p>
      <div class="list">
        @for (p of patients(); track p.patient_id) {
          <article class="card">
            <div class="info">
              <h2>{{ p.first_name }} {{ p.last_name }} <span class="muted">({{ p.mrn }})</span></h2>
              <p>{{ p.gender }} · Born {{ p.date_of_birth | date: 'd MMM y' }}</p>
              <p class="muted">Guardian: {{ p.guardian_name }} · {{ p.guardian_mobile }}</p>
            </div>

            @if (assigning() === p.patient_id) {
              <div class="assign">
                <select #d>
                  <option value="">Choose a doctor</option>
                  @for (doc of doctors(); track doc.doctor_id) {
                    <option [value]="doc.doctor_id">Dr. {{ doc.first_name }} {{ doc.last_name }} ({{ doc.specialty }})</option>
                  }
                </select>
                <button type="button" class="primary" [disabled]="!d.value" (click)="assign(p, d.value)">Assign</button>
                <button type="button" class="secondary" (click)="assigning.set(null)">Cancel</button>
              </div>
            } @else {
              <button type="button" class="secondary" (click)="assigning.set(p.patient_id)">Assign doctor</button>
            }
          </article>
        } @empty {
          <div class="card"><p class="muted">No patients found.</p></div>
        }
      </div>

      <div class="pager">
        <button type="button" class="secondary" [disabled]="page() <= 1" (click)="go(page() - 1)">Previous</button>
        <button type="button" class="secondary" [disabled]="page() >= totalPages()" (click)="go(page() + 1)">Next</button>
      </div>
    }
  `,
  styles: `
    h1 { margin: 0 0 1rem; color: #4b3a8a; }
    .searchbar { display: flex; gap: .5rem; margin-bottom: .75rem; }
    .searchbar input { flex: 1; padding: .6rem; border: 1px solid #d6d0ea; border-radius: 8px; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .card h2 { margin: 0; font-size: 1.05rem; }
    .card p { margin: .2rem 0; font-size: .9rem; }
    .assign { display: flex; gap: .5rem; flex-wrap: wrap; align-items: center; }
    .assign select { padding: .5rem; border: 1px solid #d6d0ea; border-radius: 8px; max-width: 260px; }
    .primary { padding: .5rem 1rem; border: 0; border-radius: 8px; background: #4b3a8a; color: #fff; cursor: pointer; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .secondary { padding: .5rem 1rem; border: 1px solid #4b3a8a; background: #fff; color: #4b3a8a; border-radius: 8px; cursor: pointer; }
    .secondary:disabled { opacity: .5; cursor: not-allowed; }
    .pager { display: flex; justify-content: center; gap: .75rem; margin-top: 1rem; }
    .muted { color: #6b6785; }
    .err { color: #b3261e; }
    .ok { color: #1b7f3b; }
    @media (max-width: 700px) { .card { flex-direction: column; align-items: flex-start; } }
  `,
})
export class ManagePatients implements OnInit {
  private api = inject(AdminApi);
  private pageSize = 10;
  private query = '';

  patients = signal<PatientSummary[]>([]);
  doctors = signal<DoctorSummary[]>([]);
  page = signal(1);
  total = signal(0);
  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));

  loading = signal(false);
  error = signal<string | null>(null);
  message = signal<string | null>(null);
  assigning = signal<number | null>(null);

  ngOnInit() {
    this.api.doctors().subscribe({ next: (rows) => this.doctors.set(rows), error: () => {} });
    this.load();
  }

  search(q: string) {
    this.query = q;
    this.page.set(1);
    this.load();
  }

  go(page: number) {
    this.page.set(page);
    this.load();
  }

  private load() {
    this.loading.set(true);
    this.error.set(null);
    this.api.patients(this.query, this.page(), this.pageSize).subscribe({
      next: (res) => {
        this.patients.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(errorMessage(e, 'Could not load patients.'));
      },
    });
  }

  assign(patient: PatientSummary, doctorId: string) {
    this.error.set(null);
    this.message.set(null);
    this.api.assignDoctor(patient.patient_id, Number(doctorId)).subscribe({
      next: (res) => {
        this.assigning.set(null);
        this.message.set(`${res.patient_name} is now assigned to Dr. ${res.doctor_name}.`);
      },
      error: (e: HttpErrorResponse) => this.error.set(errorMessage(e, 'Could not assign the doctor.')),
    });
  }
}