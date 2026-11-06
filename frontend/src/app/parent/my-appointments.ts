import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Appointment } from '../core/models';
import { ParentApi } from '../core/parent-api.service';

@Component({
  selector: 'app-my-appointments',
  imports: [DatePipe, RouterLink],
  template: `
    <h1>My appointments</h1>

    <div class="tabs">
      <button type="button" [class.active]="upcomingOnly()" (click)="setTab(true)">Upcoming</button>
      <button type="button" [class.active]="!upcomingOnly()" (click)="setTab(false)">All</button>
    </div>

    @if (error()) {
      <p class="err">{{ error() }}</p>
    }

    @if (loading()) {
      <p class="muted">Loading…</p>
    } @else {
      <div class="list">
        @for (a of appointments(); track a.appointment_ref) {
          <article class="card">
            <div class="when">
              <div class="day">{{ a.scheduled_at | date: 'd MMM' }}</div>
              <div class="time">{{ a.scheduled_at | date: 'shortTime' }}</div>
            </div>

            <div class="info">
              <h2>{{ a.doctor_name }}</h2>
              <p>For {{ a.patient_name }} <span class="muted">({{ a.mrn }})</span></p>
              @if (a.reason_for_visit) {
                <p class="muted">Reason: {{ a.reason_for_visit }}</p>
              }
              <p class="muted">Ref {{ a.appointment_ref }} · {{ a.duration_minutes }} min</p>
            </div>

            <div class="side">
              <span class="badge" [class]="a.status">{{ a.status }}</span>

              @if (canCancel(a)) {
                @if (confirming() === a.appointment_ref) {
                  <div class="confirm">
                    <span>Cancel this appointment?</span>
                    <button type="button" class="danger" [disabled]="cancelling()" (click)="cancel(a)">
                      {{ cancelling() ? 'Cancelling…' : 'Yes, cancel' }}
                    </button>
                    <button type="button" class="secondary" (click)="confirming.set(null)">Keep</button>
                  </div>
                } @else {
                  <button type="button" class="secondary" (click)="confirming.set(a.appointment_ref)">
                    Cancel
                  </button>
                }
              }
            </div>
          </article>
        } @empty {
          <div class="card empty">
            <p>No appointments to show.</p>
            <a class="primary" routerLink="/guardian/find-doctor">Find a doctor</a>
          </div>
        }
      </div>
    }
  `,
  styles: `
    h1 { margin: 0 0 1rem; color: #0b6e8a; }
    .tabs { display: flex; gap: .5rem; margin-bottom: 1rem; }
    .tabs button { padding: .45rem 1rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 999px; cursor: pointer; }
    .tabs button.active { background: #0b6e8a; color: #fff; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; gap: 1rem; align-items: flex-start; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .when { min-width: 70px; text-align: center; padding: .5rem; background: #eaf5f9; border-radius: 10px; }
    .day { font-weight: 700; color: #0b6e8a; }
    .time { font-size: .85rem; }
    .info { flex: 1; }
    .info h2 { margin: 0; font-size: 1.05rem; }
    .info p { margin: .2rem 0; font-size: .9rem; }
    .side { display: flex; flex-direction: column; align-items: flex-end; gap: .5rem; }
    .badge { padding: .2rem .7rem; border-radius: 999px; font-size: .8rem; text-transform: capitalize; background: #e7eef2; color: #35505c; }
    .badge.requested { background: #fff4d6; color: #8a5b00; }
    .badge.confirmed { background: #dff3e4; color: #1b7f3b; }
    .badge.completed { background: #e1ecf9; color: #1d4f91; }
    .badge.cancelled { background: #fde4e2; color: #b3261e; }
    .confirm { display: flex; flex-direction: column; align-items: flex-end; gap: .35rem; font-size: .85rem; }
    .secondary { padding: .4rem .9rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 8px; cursor: pointer; }
    .danger { padding: .4rem .9rem; border: 0; background: #b3261e; color: #fff; border-radius: 8px; cursor: pointer; }
    .danger:disabled { opacity: .5; }
    .primary { display: inline-block; padding: .55rem 1rem; border-radius: 8px; background: #0b6e8a; color: #fff; text-decoration: none; }
    .empty { flex-direction: column; align-items: center; }
    .muted { color: #5b7480; }
    .err { color: #b3261e; }
    @media (max-width: 600px) { .card { flex-wrap: wrap; } .side { align-items: flex-start; } }
  `,
})
export class MyAppointments implements OnInit {
  private api = inject(ParentApi);

  appointments = signal<Appointment[]>([]);
  upcomingOnly = signal(true);
  loading = signal(false);
  cancelling = signal(false);
  confirming = signal<string | null>(null);
  error = signal<string | null>(null);

  ngOnInit() {
    this.load();
  }

  setTab(upcomingOnly: boolean) {
    this.upcomingOnly.set(upcomingOnly);
    this.confirming.set(null);
    this.load();
  }

  canCancel(a: Appointment): boolean {
    return a.status !== 'cancelled' && a.status !== 'completed';
  }

  load() {
    this.loading.set(true);
    this.error.set(null);
    this.api.appointments(this.upcomingOnly()).subscribe({
      next: (rows) => {
        this.appointments.set(rows);
        this.loading.set(false);
      },
      error: (e) => {
        this.loading.set(false);
        this.error.set(this.errorText(e, 'Could not load appointments.'));
      },
    });
  }

  cancel(appointment: Appointment) {
    this.cancelling.set(true);
    this.error.set(null);
    this.api.cancel(appointment.appointment_ref, null).subscribe({
      next: (updated) => {
        this.cancelling.set(false);
        this.confirming.set(null);
        this.appointments.update((list) =>
          list.map((a) => (a.appointment_ref === updated.appointment_ref ? updated : a)),
        );
      },
      error: (e) => {
        this.cancelling.set(false);
        this.error.set(this.errorText(e, 'Could not cancel this appointment.'));
      },
    });
  }

  private errorText(err: HttpErrorResponse, fallback: string): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    return err.status === 0 ? 'Cannot reach the server. Is the backend running?' : fallback;
  }
}