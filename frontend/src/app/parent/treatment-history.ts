
import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';

import { PatientSummary } from '../core/models';
import { ParentApi } from '../core/parent-api.service';

@Component({
  selector: 'app-treatment-history',
  standalone: true,
  imports: [DatePipe],

  template: `
    <h1>Treatment history</h1>

    <section class="card">
      <label>
        Child

        <select (change)="onChild($event)">
          <option value="">Select a child</option>

          @for (c of children(); track c.patient_id) {
            <option
              [value]="c.patient_id"
              [selected]="patientId() === c.patient_id"
            >
              {{ c.first_name }} {{ c.last_name }} ({{ c.mrn }})
            </option>
          }
        </select>
      </label>
    </section>

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading records…</p>
    } @else if (patientId() !== null) {

      @for (r of records(); track r.treatment_record_id) {
        <article class="card record">

          <header>
            <div>
              <h2>{{ r.visit_date | date: 'd MMM y' }}</h2>
              <p class="muted">{{ r.doctor_name }}</p>
            </div>

            <span class="badge">{{ r.record_status }}</span>
          </header>

          <p class="label">Diagnosis</p>
          <p>{{ r.diagnosis }}</p>

          @if (r.medications?.length) {
            <p class="label">Medicines</p>

            <ul>
              @for (m of r.medications; track $index) {
                <li>
                  <strong>{{ m.medication_name }}</strong>

                  @if (m.dosage) {
                    · {{ m.dosage }}
                  }

                  @if (m.frequency) {
                    · {{ m.frequency }}
                  }

                  @if (m.duration) {
                    · {{ m.duration }}
                  }

                  @if (m.instructions) {
                    <div class="muted">
                      {{ m.instructions }}
                    </div>
                  }
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
            <p class="label">Doctor's notes</p>
            <p>{{ r.clinical_notes }}</p>
          }

        </article>
      } @empty {
        <div class="card">
          <p class="muted">
            No treatment records for this child yet.
          </p>
        </div>
      }
    }
  `,

  styles: `
    h1 {
      margin: 0 0 1rem;
      color: #0b6e8a;
    }

    .card {
      margin-bottom: 1rem;
      padding: 1.25rem;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 16px rgb(0 0 0 / 6%);
    }

    label {
      display: block;
      font-size: .9rem;
    }

    select {
      width: 100%;
      box-sizing: border-box;
      margin-top: .25rem;
      padding: .6rem;
      border: 1px solid #cfe3ec;
      border-radius: 8px;
      background: #fff;
    }

    .record header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .record h2 {
      margin: 0;
      font-size: 1.1rem;
    }

    .record p {
      margin: .2rem 0;
    }

    .label {
      margin-top: .9rem;
      font-size: .8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .04em;
      color: #0b6e8a;
    }

    ul {
      margin: .2rem 0;
      padding-left: 1.2rem;
    }

    li {
      margin: .35rem 0;
    }

    .badge {
      padding: .2rem .7rem;
      border-radius: 999px;
      font-size: .8rem;
      background: #e1ecf9;
      color: #1d4f91;
      text-transform: capitalize;
    }

    .muted {
      color: #5b7480;
      font-size: .9rem;
    }

    .err {
      color: #b3261e;
    }
  `,
})
export class TreatmentHistory implements OnInit {

  private api = inject(ParentApi);

  children = signal<PatientSummary[]>([]);
  patientId = signal<number | null>(null);
  records = signal<any[]>([]);

  loading = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.api.myChildren().subscribe({
      next: (rows: PatientSummary[]) => {
        this.children.set(rows);

        if (rows.length === 1) {
          this.patientId.set(rows[0].patient_id);
          this.load();
        }
      },

      error: (e: HttpErrorResponse) => {
        this.error.set(
          this.errorText(e, 'Could not load your children.')
        );
      },
    });
  }

  onChild(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;

    this.patientId.set(value ? Number(value) : null);
    this.records.set([]);

    if (value) {
      this.load();
    }
  }

  private load(): void {
    const id = this.patientId();

    if (id === null) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    this.api.treatmentHistory(id).subscribe({
      next: (rows: any[]) => {
        this.records.set(rows);
        this.loading.set(false);
      },

      error: (e: HttpErrorResponse) => {
        this.loading.set(false);

        this.error.set(
          this.errorText(e, 'Could not load treatment records.')
        );
      },
    });
  }

  private errorText(
    err: HttpErrorResponse,
    fallback: string
  ): string {
    const detail = err.error?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    return err.status === 0
      ? 'Cannot reach the server. Is the backend running?'
      : fallback;
  }
}
