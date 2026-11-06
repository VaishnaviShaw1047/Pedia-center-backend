import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { API_URL } from './config';
import {
  AssignmentResponse,
  Availability,
  AvailabilityRequest,
  DoctorCreateRequest,
  DoctorCreateResponse,
  DoctorPublic,
  DoctorSummary,
  PageResult,
  PatientSummary,
  UserCreateRequest,
  UserRow,
} from './models';

@Injectable({ providedIn: 'root' })
export class AdminApi {
  private http = inject(HttpClient);

  private search(search: string): HttpParams {
    let params = new HttpParams();
    if (search.trim()) params = params.set('search', search.trim());
    return params;
  }

  doctors(search = '') {
    return this.http.get<DoctorSummary[]>(`${API_URL}/doctors`, { params: this.search(search) });
  }

  doctor(id: number) {
    return this.http.get<DoctorPublic>(`${API_URL}/doctors/${id}`);
  }

  createDoctor(payload: DoctorCreateRequest) {
    return this.http.post<DoctorCreateResponse>(`${API_URL}/doctors`, payload);
  }

  availability(doctorId: number) {
    return this.http.get<Availability[]>(`${API_URL}/doctors/${doctorId}/availability`);
  }

  addAvailability(doctorId: number, payload: AvailabilityRequest) {
    return this.http.post<Availability>(`${API_URL}/doctors/${doctorId}/availability`, payload);
  }

  patients(search: string, page: number, pageSize: number) {
    const params = this.search(search).set('page', page).set('page_size', pageSize);
    return this.http.get<PageResult<PatientSummary>>(`${API_URL}/patients`, { params });
  }

  assignDoctor(patientId: number, doctorId: number) {
    return this.http.post<AssignmentResponse>(`${API_URL}/doctor-assignments/`, {
      patient_id: patientId,
      doctor_id: doctorId,
    });
  }

  users(search: string, page: number, pageSize: number) {
    const params = this.search(search).set('page', page).set('page_size', pageSize);
    return this.http.get<PageResult<UserRow>>(`${API_URL}/users`, { params });
  }

  createUser(payload: UserCreateRequest) {
    return this.http.post<UserRow>(`${API_URL}/users`, payload);
  }

  resetPassword(userId: number, newPassword: string) {
    return this.http.post<{ message: string }>(`${API_URL}/users/${userId}/reset-password`, {
      current_password: '',
      new_password: newPassword,
    });
  }
}