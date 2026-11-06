import { HttpErrorResponse } from '@angular/common/http';

export function errorMessage(err: HttpErrorResponse, fallback: string): string {
  const detail = err.error?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg: string }) => `${(d.loc ?? []).slice(1).join(' > ')}: ${d.msg}`)
      .join('; ');
  }
  return err.status === 0 ? 'Cannot reach the server. Is the backend running?' : fallback;
}