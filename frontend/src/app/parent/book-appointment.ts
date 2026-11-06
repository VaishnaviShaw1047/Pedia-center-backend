import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Appointment, DoctorPublic, PatientSummary } from '../core/models';
import { ParentApi } from '../core/parent-api.service';

@Component({
  selector: 'app-book-appointment',
  imports: [RouterLink, DatePipe],
  template: `
    <a class="back" routerLink="/guardian/find-doctor">← Back to doctors</a>

    @if (booked(); as b) {
      <section class="card success">
        <h1>Appointment booked</h1>
        <p>
          <strong>{{ b.patient_name }}</strong> with <strong>{{ b.doctor_name }}</strong>
        </p>
        <p>
          {{ b.scheduled_at | date: 'fullDate' }} at {{ b.scheduled_at | date: 'shortTime' }}
          ({{ b.duration_minutes }} min)
        </p>
        <p>Reference: <strong>{{ b.appointment_ref }}</strong></p>
        <div class="row">
          <a class="primary" routerLink="/guardian/my-appointments">View my appointments</a>
          <a class="secondary" routerLink="/guardian/find-doctor">Book another</a>
        </div>
      </section>
    } @else {
      <h1>Book an appointment</h1>

      @if (doctor(); as d) {
        <section class="card doctor">
          <h2>Dr. {{ d.first_name }} {{ d.last_name }}</h2>
          <p class="sub">{{ d.specialty }} · {{ d.qualification }}</p>
          <p>Consultation fee: ₹{{ d.consultation_fee }}</p>
          @if (d.available_days) {
            <p class="muted">Usually available: {{ d.available_days }}</p>
          }
        </section>
      }

      @if (loading()) {
        <p class="muted">Loading…</p>
      } @else {
        <section class="card">
          <label>
            Child
            <select (change)="onChild($event)">
              <option value="">Select a child</option>
              @for (c of children(); track c.patient_id) {
                <option [value]="c.patient_id" [selected]="patientId() === c.patient_id">
                  {{ c.first_name }} {{ c.last_name }} ({{ c.mrn }})
                </option>
              }
            </select>
          </label>
          @if (children().length === 0) {
            <p class="err">No children were found on your account.</p>
          }

          <label>
            Date
            <input type="date" [min]="today" [value]="date()" (change)="onDate($event)" />
          </label>

          @if (date()) {
            <div class="slots-box">
              <p class="label">Available times</p>
              @if (loadingSlots()) {
                <p class="muted">Checking availability…</p>
              } @else if (slots().length === 0) {
                <p class="muted">No free slots on this date. Try another day.</p>
              } @else {
                <div class="slots">
                  @for (s of slots(); track s) {
                    <button
                      type="button"
                      class="slot"
                      [class.selected]="slot() === s"
                      (click)="slot.set(s)"
                    >
                      {{ s }}
                    </button>
                  }
                </div>
              }
            </div>
          }

          <label>
            Reason for visit (optional)
            <textarea
              rows="3"
              maxlength="255"
              [value]="reason()"
              (input)="onReason($event)"
              placeholder="e.g. Fever for two days"
            ></textarea>
          </label>

          @if (error()) {
            <p class="err">{{ error() }}</p>
          }

          <button type="button" class="primary wide" [disabled]="!canBook() || submitting()" (click)="submit()">
            {{ submitting() ? 'Booking…' : 'Confirm booking' }}
          </button>
        </section>
      }
    }
  `,
  styles: `
    .back { display: inline-block; margin-bottom: .75rem; color: #0b6e8a; text-decoration: none; }
    h1 { margin: 0 0 1rem; color: #0b6e8a; }
    h2 { margin: 0; font-size: 1.15rem; }
    .card { margin-bottom: 1rem; padding: 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .card p { margin: .25rem 0; }
    .sub { color: #0b6e8a; font-weight: 600; }
    .muted { color: #5b7480; font-size: .9rem; }
    .err { color: #b3261e; font-size: .9rem; }
    label { display: block; margin-top: 1rem; font-size: .9rem; }
    input, select, textarea { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #cfe3ec; border-radius: 8px; background: #fff; font-family: inherit; }
    .label { margin: 1rem 0 .4rem; font-size: .9rem; }
    .slots { display: flex; flex-wrap: wrap; gap: .5rem; }
    .slot { padding: .45rem .9rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 999px; cursor: pointer; }
    .slot.selected { background: #0b6e8a; color: #fff; }
    .primary { display: inline-block; padding: .65rem 1.2rem; border: 0; border-radius: 8px; background: #0b6e8a; color: #fff; text-decoration: none; cursor: pointer; text-align: center; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .wide { width: 100%; box-sizing: border-box; margin-top: 1.25rem; }
    .secondary { display: inline-block; padding: .65rem 1.2rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 8px; text-decoration: none; }
    .row { display: flex; gap: .75rem; margin-top: 1rem; flex-wrap: wrap; }
    .success h1 { color: #1b7f3b; }
  `,
})
export class BookAppointment implements OnInit {
  private api = inject(ParentApi);
  private route = inject(ActivatedRoute);

  doctorId = Number(this.route.snapshot.paramMap.get('doctorId'));
  today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);

  doctor = signal<DoctorPublic | null>(null);
  children = signal<PatientSummary[]>([]);
  slots = signal<string[]>([]);

  patientId = signal<number | null>(null);
  date = signal('');
  slot = signal<string | null>(null);
  reason = signal('');

  loading = signal(true);
  loadingSlots = signal(false);
  submitting = signal(false);
  error = signal<string | null>(null);
  booked = signal<Appointment | null>(null);

  canBook = computed(() => this.patientId() !== null && !!this.date() && !!this.slot());

  ngOnInit() {
    if (!Number.isInteger(this.doctorId)) {
      this.error.set('Invalid doctor.');
      this.loading.set(false);
      return;
    }

    this.api.doctor(this.doctorId).subscribe({
      next: (d) => this.doctor.set(d),
      error: (e) => this.error.set(this.errorText(e, 'Could not load this doctor.')),
    });

    this.api.myChildren().subscribe({
      next: (rows) => {
        this.children.set(rows);
        if (rows.length === 1) this.patientId.set(rows[0].patient_id);
        this.loading.set(false);
      },
      error: (e) => {
        this.loading.set(false);
        this.error.set(this.errorText(e, 'Could not load your children.'));
      },
    });
  }

  onChild(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    this.patientId.set(value ? Number(value) : null);
  }

  onDate(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.date.set(value);
    this.slot.set(null);
    this.error.set(null);
    if (value) this.loadSlots();
    else this.slots.set([]);
  }

  onReason(event: Event) {
    this.reason.set((event.target as HTMLTextAreaElement).value);
  }

  private loadSlots() {
    this.loadingSlots.set(true);
    this.api.slots(this.doctorId, this.date()).subscribe({
      next: (res) => {
        this.slots.set(res.slots);
        this.loadingSlots.set(false);
      },
      error: (e) => {
        this.slots.set([]);
        this.loadingSlots.set(false);
        this.error.set(this.errorText(e, 'Could not load time slots.'));
      },
    });
  }

  submit() {
    if (!this.canBook()) return;
    this.submitting.set(true);
    this.error.set(null);

    this.api
      .book({
        doctor_id: this.doctorId,
        patient_id: this.patientId()!,
        scheduled_at: `${this.date()}T${this.slot()}:00`,
        reason_for_visit: this.reason().trim() || null,
      })
      .subscribe({
        next: (appointment) => {
          this.submitting.set(false);
          this.booked.set(appointment);
        },
        error: (e) => {
          this.submitting.set(false);
          this.error.set(this.errorText(e, 'Booking failed. Please try again.'));
          // The slot may have just been taken, so refresh the list.
          this.slot.set(null);
          this.loadSlots();
        },
      });
  }

  private errorText(err: HttpErrorResponse, fallback: string): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg: string }) => d.msg).join('; ');
    }
    return err.status === 0 ? 'Cannot reach the server. Is the backend running?' : fallback;
  }
}