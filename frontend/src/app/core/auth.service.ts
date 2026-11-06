import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { map } from 'rxjs';
import { API_URL } from './config';
import {
  AuthTokenResponse,
  DoctorTokenResponse,
  RegistrationRequest,
  RegistrationResponse,
  Role,
} from './models';

export interface Session {
  token: string;
  role: Role;
  userId: number;
  name?: string;
  mustChangePassword?: boolean;
}

const STORAGE_KEY = 'pc_session';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private _session = signal<Session | null>(this.restore());
  readonly session = this._session.asReadonly();
  readonly role = computed(() => this._session()?.role ?? null);

  get token(): string | null {
    return this._session()?.token ?? null;
  }

  loginGuardian(mobile: string, password: string) {
    return this.http
      .post<AuthTokenResponse>(`${API_URL}/auth/login`, { mobile_number: mobile, password })
      .pipe(map((r) => this.start(r.access_token, 'guardian')));
  }

  loginDoctor(staffId: string, password: string) {
    return this.http
      .post<DoctorTokenResponse>(`${API_URL}/auth/doctor-login`, { staff_id: staffId, password })
      .pipe(
        map((r) =>
          this.start(r.access_token, 'doctor', {
            name: r.doctor_name,
            mustChangePassword: r.must_change_password,
          }),
        ),
      );
  }

 loginAdmin(username: string, password: string) {
  debugger;

  return this.http
    .post<AuthTokenResponse>(
      `${API_URL}/auth/admin-login`,
      { username, password }
    )
    .pipe(
      map((r) => {
        debugger;
        console.log('Admin login response:', r);
        console.log('Access token:', r.access_token);
        return this.start(r.access_token, 'admin');
      })
    );
}

    register(payload: RegistrationRequest) {
    return this.http.post<RegistrationResponse>(`${API_URL}/registration`, payload);
  }
    markPasswordChanged() {
    const s = this._session();
    if (!s) return;
    const updated = { ...s, mustChangePassword: false };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    this._session.set(updated);
  }

  logout() {
    localStorage.removeItem(STORAGE_KEY);
    this._session.set(null);
    this.router.navigate(['/login']);
  }

  private start(token: string, role: Role, extra: Partial<Session> = {}): Session {
    const claims = this.decode(token);
    const session: Session = { token, role, userId: Number(claims?.sub), ...extra };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    this._session.set(session);
    return session;
  }

  private restore(): Session | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const session: Session = JSON.parse(raw);
      const exp = this.decode(session.token)?.exp;
      if (exp && exp * 1000 < Date.now()) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      return session;
    } catch {
      return null;
    }
  }

  private decode(token: string): { sub?: string; exp?: number } | null {
    try {
      const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(payload));
    } catch {
      return null;
    }
  }
}
