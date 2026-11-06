import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { DoctorApi } from '../core/doctor-api.service';
import { TreatmentRecordRequest } from '../core/models';

@Component({
  selector: 'app-add-record',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <a class="back" [routerLink]="['/doctor/patients', patientId]">← Back to history</a>
    <h1>Add treatment record</h1>
    @if (patientName()) {
      <p class="muted">Patient: <strong>{{ patientName() }}</strong></p>
    }

    <form class="card" [formGroup]="form" (ngSubmit)="submit()" novalidate>
      <label>
        Visit date and time
        <input type="datetime-local" formControlName="visit_date" />
      </label>

      <label>
        Diagnosis
        <textarea rows="2" maxlength="500" formControlName="diagnosis"></textarea>
      </label>
      @if (form.controls.diagnosis.touched && form.controls.diagnosis.invalid) {
        <small class="err">Diagnosis is required</small>
      }

      <h2>Medicines</h2>
      <div formArrayName="medications">
        @for (m of medications.controls; track m; let i = $index) {
          <div class="med" [formGroupName]="i">
            <div class="grid">
              <label>Name <input formControlName="medication_name" /></label>
              <label>Dosage <input formControlName="dosage" placeholder="e.g. 5 ml" /></label>
              <label>Frequency <input formControlName="frequency" placeholder="e.g. Twice a day" /></label>
              <label>Duration <input formControlName="duration" placeholder="e.g. 5 days" /></label>
            </div>
            <label>Instructions <input formControlName="instructions" /></label>
            <button type="button" class="link" (click)="removeMedication(i)">Remove</button>
          </div>
        }
      </div>
      <button type="button" class="secondary" (click)="addMedication()">+ Add medicine</button>

      <label>
        Treatment plan (optional)
        <textarea rows="3" maxlength="1000" formControlName="treatment_plan"></textarea>
      </label>

      <label>
        Follow-up date (optional)
        <input type="date" formControlName="follow_up_date" />
      </label>

      <label>
        Clinical notes (optional)
        <textarea rows="3" maxlength="2000" formControlName="clinical_notes"></textarea>
      </label>

      @if (error()) {
        <p class="err">{{ error() }}</p>
      }

      <button class="primary" type="submit" [disabled]="saving()">
        {{ saving() ? 'Saving…' : 'Save record' }}
      </button>
    </form>
  `,
  styles: `
    .back { display: inline-block; margin-bottom: .75rem; color: #1d4f91; text-decoration: none; }
    h1 { margin: 0 0 .5rem; color: #1d4f91; }
    h2 { margin: 1.5rem 0 .5rem; font-size: 1.05rem; color: #1d4f91; }
    .card { padding: 1.5rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    label { display: block; margin-top: .85rem; font-size: .9rem; }
    input, textarea { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #cfdcec; border-radius: 8px; font-family: inherit; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0 1rem; }
    .med { padding: .75rem 1rem; margin-bottom: .75rem; border: 1px solid #e0e9f5; border-radius: 10px; background: #fafcff; }
    .link { border: 0; background: none; color: #b3261e; cursor: pointer; margin-top: .4rem; }
    .secondary { margin-top: .25rem; padding: .45rem 1rem; border: 1px solid #1d4f91; background: #fff; color: #1d4f91; border-radius: 8px; cursor: pointer; }
    .primary { width: 100%; margin-top: 1.5rem; padding: .75rem; border: 0; border-radius: 8px; background: #1d4f91; color: #fff; cursor: pointer; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .muted { color: #5b7480; }
    .err { color: #b3261e; font-size: .85rem; }
  `,
})
export class AddRecord implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private api = inject(DoctorApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  patientId = Number(this.route.snapshot.paramMap.get('patientId'));
  appointmentId = this.route.snapshot.queryParamMap.get('appointmentId');

  patientName = signal('');
  saving = signal(false);
  error = signal<string | null>(null);

  form = this.fb.group({
    visit_date: [this.nowLocal(), Validators.required],
    diagnosis: ['', [Validators.required, Validators.maxLength(500)]],
    medications: this.fb.array([this.newMedication()]),
    treatment_plan: [''],
    follow_up_date: [''],
    clinical_notes: [''],
  });

  get medications() {
    return this.form.controls.medications;
  }

  ngOnInit() {
    this.api.patients().subscribe({
      next: (rows) => {
        const p = rows.find((x) => x.patient_id === this.patientId);
        if (p) this.patientName.set(`${p.first_name} ${p.last_name} (${p.mrn})`);
      },
      error: () => {},
    });
  }

  private nowLocal(): string {
    return new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  }

  private newMedication() {
    return this.fb.group({
      medication_name: [''],
      dosage: [''],
      frequency: [''],
      duration: [''],
      instructions: [''],
    });
  }

  addMedication() {
    this.medications.push(this.newMedication());
  }

  removeMedication(index: number) {
    this.medications.removeAt(index);
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue();
    const orNull = (s: string) => (s && s.trim() ? s.trim() : null);

    const payload: TreatmentRecordRequest = {
      patient_id: this.patientId,
      appointment_id: this.appointmentId ? Number(this.appointmentId) : null,
      visit_date: `${v.visit_date}:00`,
      diagnosis: v.diagnosis.trim(),
      medications: v.medications
        .filter((m) => m.medication_name.trim())
        .map((m) => ({
          medication_name: m.medication_name.trim(),
          dosage: orNull(m.dosage),
          frequency: orNull(m.frequency),
          duration: orNull(m.duration),
          instructions: orNull(m.instructions),
        })),
      treatment_plan: orNull(v.treatment_plan),
      follow_up_date: v.follow_up_date ? `${v.follow_up_date}T00:00:00` : null,
      clinical_notes: orNull(v.clinical_notes),
    };

    this.saving.set(true);
    this.error.set(null);

    this.api.addRecord(payload).subscribe({
      next: () => this.router.navigate(['/doctor/patients', this.patientId]),
      error: (e: HttpErrorResponse) => {
        this.saving.set(false);
        const detail = e.error?.detail;
        this.error.set(
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg: string }) => d.msg).join('; ')
              : 'Could not save the record.',
        );
      },
    });
  }
}