
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { API_URL } from './config';

import {
  Appointment,
  BookingRequest,
  DoctorPublic,
  PatientSummary,
  SlotsResponse,
  SpecialtyCount,
} from './models';

export interface DoctorFilters {
  specialty?: string;
  language?: string;
  max_fee?: number | null;
  day?: string;
}

@Injectable({ providedIn: 'root' })
export class ParentApi {
  private http = inject(HttpClient);

  specialties() {
    return this.http.get<SpecialtyCount[]>(
      `${API_URL}/doctors/specialties`
    );
  }

  doctors(filters: DoctorFilters = {}) {
    let params = new HttpParams();

    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    }

    return this.http.get<DoctorPublic[]>(
      `${API_URL}/doctors/available`,
      { params }
    );
  }

  doctor(id: number) {
    return this.http.get<DoctorPublic>(
      `${API_URL}/doctors/${id}`
    );
  }

  slots(doctorId: number, date: string) {
    return this.http.get<SlotsResponse>(
      `${API_URL}/doctors/${doctorId}/slots`,
      { params: { date } }
    );
  }

  myChildren() {
    return this.http.get<PatientSummary[]>(
      `${API_URL}/patients/mine`
    );
  }

  appointments(upcomingOnly: boolean) {
    return this.http.get<Appointment[]>(
      `${API_URL}/appointments`,
      { params: { upcoming_only: upcomingOnly } }
    );
  }

  book(payload: BookingRequest) {
    return this.http.post<Appointment>(
      `${API_URL}/appointments`,
      payload
    );
  }

  cancel(ref: string, reason: string | null) {
    return this.http.patch<Appointment>(
      `${API_URL}/appointments/${ref}/cancel`,
      { reason }
    );
  }

  treatmentHistory(patientId: number) {
    return this.http.get<any[]>(
      `${API_URL}/patients/${patientId}/treatment-history`
    );
  }
}
