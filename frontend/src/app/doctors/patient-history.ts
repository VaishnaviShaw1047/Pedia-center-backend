import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DoctorApi } from '../core/doctor-api.service';
import { TreatmentRecord } from '../core/models';

@Component({
  selector: 'app-patient-history',
  imports: [DatePipe, RouterLink],
  template: `
    <a class="back" routerLink="/doctor/patients">← Back to patients</a>

    <div class="head">
      <h1>Treatment history</h1>
      <a class="primary" [routerLink]="['/doctor/patients', patientId, 'add-record']">Add record</a>
    </div>

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading records…</p>
    } @else {
      @for (r of records(); track r.treatment_record_id) {
        <article class="card">
          <header>
            <div>
              <h2>{{ r.visit_date | date: 'd MMM y' }}</h2>
              <p class="muted">{{ r.patient_name }} · {{ r.doctor_name }}</p>
            </div>
            <span class="badge">{{ r.record_status }}</span>
          </header>

          <p class="label">Diagnosis</p>
          <p>{{ r.diagnosis }}</p>

          @if (r.medications.length) {
            <p class="label">Medicines</p>
            <ul>
              @for (m of r.medications; track $index) {
                <li>
                  <strong>{{ m.medication_name }}</strong>
                  @if (m.dosage) { · {{ m.dosage }} }
                  @if (m.frequency) { · {{ m.frequency }} }
                  @if (m.duration) { · {{ m.duration }} }
                  @if (m.instructions) { <div class="muted">{{ m.instructions }}</div> }
                </li>
              }
            </ul>
          }

          @if (r.treatment_plan) {
            <p class="label">Treatment plan</p>
            <p>{{ r.treatment_plan }}</p>
          }
          @if (r.follow_up_date) {
            <p class="label">Follow-up</p>
            <p>{{ r.follow_up_date | date: 'd MMM y' }}</p>
          }
          @if (r.clinical_notes) {
            <p class="label">Clinical notes</p>
            <p>{{ r.clinical_notes }}</p>
          }
        </article>
      } @empty {
        <div class="card"><p class="muted">No treatment records for this patient yet.</p></div>
      }
    }
  `,
  styles: `
    .back { display: inline-block; margin-bottom: .75rem; color: #1d4f91; text-decoration: none; }
    .head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    h1 { margin: 0; color: #1d4f91; }
    .primary { padding: .5rem 1rem; border-radius: 8px; background: #1d4f91; color: #fff; text-decoration: none; }
    .card { margin-bottom: 1rem; padding: 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .card header { display: flex; justify-content: space-between; align-items: flex-start; }
    .card h2 { margin: 0; font-size: 1.1rem; }
    .card p { margin: .2rem 0; }
    .label { margin-top: .9rem; font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: #1d4f91; }
    ul { margin: .2rem 0; padding-left: 1.2rem; }
    li { margin: .35rem 0; }
    .badge { padding: .2rem .7rem; border-radius: 999px; font-size: .8rem; background: #e1ecf9; color: #1d4f91; text-transform: capitalize; }
    .muted { color: #5b7480; font-size: .9rem; }
    .err { color: #b3261e; }
  `,
})
export class PatientHistory implements OnInit {
  private api = inject(DoctorApi);
  private route = inject(ActivatedRoute);

  patientId = Number(this.route.snapshot.paramMap.get('patientId'));
  records = signal<TreatmentRecord[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.api.history(this.patientId).subscribe({
      next: (rows) => {
        this.records.set(rows);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(
          typeof e.error?.detail === 'string' ? e.error.detail : 'Could not load records.',
        );
      },
    });
  }
}