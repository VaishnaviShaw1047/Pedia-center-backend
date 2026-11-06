import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DoctorApi } from '../core/doctor-api.service';
import { Appointment } from '../core/models';

@Component({
  selector: 'app-schedule',
  imports: [DatePipe, RouterLink],
  template: `
    <h1>My schedule</h1>

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
              <h2>{{ a.patient_name }} <span class="muted">({{ a.mrn }})</span></h2>
              @if (a.reason_for_visit) {
                <p>Reason: {{ a.reason_for_visit }}</p>
              }
              <p class="muted">Ref {{ a.appointment_ref }} · {{ a.duration_minutes }} min</p>
              <div class="row">
                <a class="secondary" [routerLink]="['/doctor/patients', a.patient_id]">History</a>
                <a
                  class="primary"
                  [routerLink]="['/doctor/patients', a.patient_id, 'add-record']"
                  [queryParams]="{ appointmentId: a.appointment_id }"
                >Add record</a>
              </div>
            </div>
            <span class="badge" [class]="a.status">{{ a.status }}</span>
          </article>
        } @empty {
          <div class="card"><p class="muted">No appointments to show.</p></div>
        }
      </div>
    }
  `,
  styles: `
    h1 { margin: 0 0 1rem; color: #1d4f91; }
    .tabs { display: flex; gap: .5rem; margin-bottom: 1rem; }
    .tabs button { padding: .45rem 1rem; border: 1px solid #1d4f91; background: #fff; color: #1d4f91; border-radius: 999px; cursor: pointer; }
    .tabs button.active { background: #1d4f91; color: #fff; }
    .list { display: grid; gap: .75rem; }
    .card { display: flex; gap: 1rem; align-items: flex-start; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .when { min-width: 70px; text-align: center; padding: .5rem; background: #e8f0fa; border-radius: 10px; }
    .day { font-weight: 700; color: #1d4f91; }
    .time { font-size: .85rem; }
    .info { flex: 1; }
    .info h2 { margin: 0; font-size: 1.05rem; }
    .info p { margin: .2rem 0; font-size: .9rem; }
    .row { display: flex; gap: .5rem; margin-top: .6rem; }
    .primary { padding: .4rem .9rem; border-radius: 8px; background: #1d4f91; color: #fff; text-decoration: none; font-size: .9rem; }
    .secondary { padding: .4rem .9rem; border: 1px solid #1d4f91; border-radius: 8px; color: #1d4f91; text-decoration: none; font-size: .9rem; }
    .badge { padding: .2rem .7rem; border-radius: 999px; font-size: .8rem; text-transform: capitalize; background: #e7eef2; color: #35505c; }
    .badge.requested { background: #fff4d6; color: #8a5b00; }
    .badge.confirmed { background: #dff3e4; color: #1b7f3b; }
    .badge.completed { background: #e1ecf9; color: #1d4f91; }
    .badge.cancelled { background: #fde4e2; color: #b3261e; }
    .muted { color: #5b7480; }
    .err { color: #b3261e; }
  `,
})
export class Schedule implements OnInit {
  private api = inject(DoctorApi);

  appointments = signal<Appointment[]>([]);
  upcomingOnly = signal(true);
  loading = signal(false);
  error = signal<string | null>(null);

  ngOnInit() {
    this.load();
  }

  setTab(upcomingOnly: boolean) {
    this.upcomingOnly.set(upcomingOnly);
    this.load();
  }

  private load() {
    this.loading.set(true);
    this.error.set(null);
    this.api.appointments(this.upcomingOnly()).subscribe({
      next: (rows) => {
        this.appointments.set(rows);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(
          typeof e.error?.detail === 'string' ? e.error.detail : 'Could not load your schedule.',
        );
      },
    });
  }
}