import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { API_URL } from './config';
import {
  Appointment,
  DoctorProfile,
  PatientSummary,
  TreatmentRecord,
  TreatmentRecordRequest,
} from './models';

@Injectable({ providedIn: 'root' })
export class DoctorApi {
  private http = inject(HttpClient);

  profile() {
    return this.http.get<DoctorProfile>(`${API_URL}/auth/doctor/me`);
  }

  changePassword(currentPassword: string, newPassword: string) {
    return this.http.post<{ message: string }>(`${API_URL}/auth/doctor/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  appointments(upcomingOnly: boolean) {
    return this.http.get<Appointment[]>(`${API_URL}/doctor/appointments`, {
      params: { upcoming_only: upcomingOnly },
    });
  }

  patients() {
    return this.http.get<PatientSummary[]>(`${API_URL}/doctor/patients`);
  }

  history(patientId: number) {
    return this.http.get<TreatmentRecord[]>(`${API_URL}/treatment-records/${patientId}`);
  }

  addRecord(payload: TreatmentRecordRequest) {
    return this.http.post<TreatmentRecord>(`${API_URL}/treatment-records`, payload);
  }
}