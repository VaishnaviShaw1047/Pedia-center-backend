import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { RegistrationRequest, RegistrationResponse } from '../../core/models';

interface Field {
  key: string;
  label: string;
  type?: string;
  options?: string[];
}

// Child must be born in the past and be under 18 (same rule as the backend).
function underEighteen(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (!value) return null;
  const dob = new Date(value);
  const today = new Date();
  if (dob > today) return { future: true };
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) age--;
  return age >= 18 ? { adult: true } : null;
}

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirm = group.get('confirm_password')?.value;
  return password && confirm && password !== confirm ? { mismatch: true } : null;
}

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <main class="card">
      @if (result(); as res) {
        <h1>Registration successful</h1>
        <p>{{ res.message }}. Medical record numbers (MRN) for your children:</p>
        <ul>
          @for (p of res.patients; track p.patient_id) {
            <li>{{ p.first_name }}: <strong>{{ p.mrn }}</strong></li>
          }
        </ul>
        <a class="primary link" routerLink="/login">Go to sign in</a>
      } @else {
        <h1>Create your account</h1>

        <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <h2>Parent / guardian details</h2>
          <div class="grid">
            @for (f of guardianFields; track f.key) {
              <label>
                {{ f.label }}
                @if (f.options) {
                  <select [formControlName]="f.key">
                    <option value="">Select</option>
                    @for (o of f.options; track o) {
                      <option [value]="o">{{ o }}</option>
                    }
                  </select>
                } @else {
                  <input [type]="f.type ?? 'text'" [formControlName]="f.key" />
                }
                <small class="err">{{ msg(form.get(f.key)) }}</small>
              </label>
            }
          </div>
          @if (form.hasError('mismatch') && form.controls.confirm_password.touched) {
            <p class="err">Passwords do not match</p>
          }

          <h2>Children</h2>
          <div formArrayName="children">
            @for (child of children.controls; track child; let i = $index) {
              <section class="child" [formGroupName]="i">
                <div class="child-head">
                  <h3>Child {{ i + 1 }}</h3>
                  @if (children.length > 1) {
                    <button type="button" class="link-btn" (click)="removeChild(i)">Remove</button>
                  }
                </div>
                <div class="grid">
                  @for (f of childFields; track f.key) {
                    <label>
                      {{ f.label }}
                      @if (f.options) {
                        <select [formControlName]="f.key">
                          <option value="">Select</option>
                          @for (o of f.options; track o) {
                            <option [value]="o">{{ o }}</option>
                          }
                        </select>
                      } @else {
                        <input [type]="f.type ?? 'text'" [formControlName]="f.key" />
                      }
                      <small class="err">{{ msg(child.get(f.key)) }}</small>
                    </label>
                  }
                </div>
              </section>
            }
          </div>
          <button type="button" class="secondary" (click)="addChild()">+ Add another child</button>

          <h2>Consent</h2>
          <label class="check">
            <input type="checkbox" formControlName="terms_accepted" />
            I accept the terms and conditions
          </label>
          <small class="err">{{ msg(form.get('terms_accepted')) }}</small>
          <label class="check">
            <input type="checkbox" formControlName="health_data_consent" />
            I consent to the use of my child's health data
          </label>
          <small class="err">{{ msg(form.get('health_data_consent')) }}</small>

          @if (error()) {
            <p class="err banner">{{ error() }}</p>
          }

          <button class="primary" type="submit" [disabled]="loading()">
            {{ loading() ? 'Creating account…' : 'Create account' }}
          </button>
          <p class="foot">Already registered? <a routerLink="/login">Sign in</a></p>
        </form>
      }
    </main>
  `,
  styles: `
    :host { display: block; min-height: 100vh; background: #f2f7fb; font-family: system-ui, sans-serif; padding: 2rem 1rem; }
    .card { max-width: 760px; margin: 0 auto; padding: 2rem; background: #fff; border-radius: 16px; box-shadow: 0 8px 30px rgb(0 0 0 / 8%); }
    h1 { margin: 0 0 1rem; font-size: 1.6rem; color: #0b6e8a; }
    h2 { margin: 1.5rem 0 .5rem; font-size: 1.1rem; color: #0b6e8a; }
    h3 { margin: 0; font-size: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .75rem 1rem; }
    label { display: block; font-size: .9rem; }
    input:not([type='checkbox']), select { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .6rem; border: 1px solid #cfe3ec; border-radius: 8px; background: #fff; }
    .check { display: flex; gap: .5rem; align-items: center; margin-top: .75rem; }
    .child { margin: .75rem 0; padding: 1rem; border: 1px solid #e0edf3; border-radius: 12px; background: #fafdff; }
    .child-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: .5rem; }
    .link-btn { border: 0; background: none; color: #b3261e; cursor: pointer; }
    .secondary { margin-top: .5rem; padding: .5rem 1rem; border: 1px solid #0b6e8a; background: #fff; color: #0b6e8a; border-radius: 8px; cursor: pointer; }
    .primary { display: block; width: 100%; box-sizing: border-box; margin-top: 1.5rem; padding: .75rem; border: 0; border-radius: 8px; background: #0b6e8a; color: #fff; text-align: center; text-decoration: none; cursor: pointer; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .err { color: #b3261e; font-size: .8rem; min-height: 1em; display: block; }
    .banner { font-size: .9rem; margin-top: 1rem; }
    .foot { text-align: center; font-size: .9rem; }
  `,
})
export class Register {
  private fb = inject(NonNullableFormBuilder);
  private auth = inject(AuthService);

  loading = signal(false);
  error = signal<string | null>(null);
  result = signal<RegistrationResponse | null>(null);

  guardianFields: Field[] = [
    { key: 'first_name', label: 'First name' },
    { key: 'last_name', label: 'Last name' },
    { key: 'relationship_to_child', label: 'Relationship to child', options: ['Mother', 'Father', 'Guardian', 'Other'] },
    { key: 'mobile_number', label: 'Mobile number (10 digits, starts with 6-9)', type: 'tel' },
    { key: 'email', label: 'Email (optional)', type: 'email' },
    { key: 'preferred_language', label: 'Preferred language (optional)', options: ['English', 'Hindi', 'Bengali'] },
    { key: 'password', label: 'Password (minimum 8 characters)', type: 'password' },
    { key: 'confirm_password', label: 'Confirm password', type: 'password' },
    { key: 'address_line1', label: 'Address line 1' },
    { key: 'address_line2', label: 'Address line 2 (optional)' },
    { key: 'city', label: 'City' },
    { key: 'state', label: 'State' },
    { key: 'pincode', label: 'Pincode (6 digits)' },
  ];

  childFields: Field[] = [
    { key: 'first_name', label: 'First name' },
    { key: 'last_name', label: 'Last name' },
    { key: 'date_of_birth', label: 'Date of birth', type: 'date' },
    { key: 'gender', label: 'Gender', options: ['Male', 'Female', 'Other'] },
    { key: 'blood_group', label: 'Blood group (optional)', options: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] },
    { key: 'immunization_status', label: 'Immunization status (optional)', options: ['Complete', 'Partial', 'Not started'] },
    { key: 'abha_id', label: 'ABHA ID (optional, 14 digits)' },
    { key: 'aadhaar_number', label: 'Aadhaar number (optional, 12 digits)' },
    { key: 'known_allergies', label: 'Known allergies (optional)' },
    { key: 'existing_conditions', label: 'Existing conditions (optional)' },
    { key: 'current_medications', label: 'Current medications (optional)' },
    { key: 'referred_by', label: 'Referred by (optional)' },
  ];

  form = this.fb.group(
    {
      first_name: ['', [Validators.required, Validators.maxLength(50)]],
      last_name: ['', [Validators.required, Validators.maxLength(50)]],
      relationship_to_child: ['', Validators.required],
      mobile_number: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
      email: ['', Validators.email],
      preferred_language: [''],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', Validators.required],
      address_line1: ['', [Validators.required, Validators.maxLength(100)]],
      address_line2: ['', Validators.maxLength(100)],
      city: ['', [Validators.required, Validators.maxLength(50)]],
      state: ['', [Validators.required, Validators.maxLength(50)]],
      pincode: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]],
      terms_accepted: [false, Validators.requiredTrue],
      health_data_consent: [false, Validators.requiredTrue],
      children: this.fb.array([this.newChild()]),
    },
    { validators: passwordsMatch },
  );

  get children() {
    return this.form.controls.children;
  }

  private newChild() {
    return this.fb.group({
      first_name: ['', [Validators.required, Validators.maxLength(50)]],
      last_name: ['', [Validators.required, Validators.maxLength(50)]],
      date_of_birth: ['', [Validators.required, underEighteen]],
      gender: ['', Validators.required],
      blood_group: [''],
      immunization_status: [''],
      abha_id: ['', Validators.pattern(/^\d{14}$/)],
      aadhaar_number: ['', Validators.pattern(/^[2-9]\d{11}$/)],
      known_allergies: ['', Validators.maxLength(255)],
      existing_conditions: ['', Validators.maxLength(500)],
      current_medications: ['', Validators.maxLength(255)],
      referred_by: ['', Validators.maxLength(100)],
    });
  }

  addChild() {
    this.children.push(this.newChild());
  }

  removeChild(index: number) {
    if (this.children.length > 1) this.children.removeAt(index);
  }

  msg(control: AbstractControl | null): string {
    if (!control || !control.touched || !control.errors) return '';
    const e = control.errors;
    if (e['required'] || e['requiredTrue']) return 'This is required';
    if (e['pattern']) return 'Invalid format';
    if (e['email']) return 'Enter a valid email';
    if (e['minlength']) return `Minimum ${e['minlength'].requiredLength} characters`;
    if (e['maxlength']) return `Maximum ${e['maxlength'].requiredLength} characters`;
    if (e['future']) return 'Date cannot be in the future';
    if (e['adult']) return 'Child must be under 18';
    return 'Invalid value';
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error.set('Please fix the highlighted fields.');
      return;
    }

    const v = this.form.getRawValue();
    const orNull = (s: string) => (s && s.trim() ? s.trim() : null);

    const payload: RegistrationRequest = {
      first_name: v.first_name.trim(),
      last_name: v.last_name.trim(),
      relationship_to_child: v.relationship_to_child,
      mobile_number: v.mobile_number,
      email: orNull(v.email),
      password: v.password,
      address_line1: v.address_line1.trim(),
      address_line2: orNull(v.address_line2),
      city: v.city.trim(),
      state: v.state.trim(),
      pincode: v.pincode,
      preferred_language: orNull(v.preferred_language),
      terms_accepted: v.terms_accepted,
      health_data_consent: v.health_data_consent,
      children: v.children.map((c) => ({
        first_name: c.first_name.trim(),
        last_name: c.last_name.trim(),
        date_of_birth: c.date_of_birth,
        gender: c.gender,
        abha_id: orNull(c.abha_id),
        aadhaar_number: orNull(c.aadhaar_number),
        blood_group: orNull(c.blood_group),
        known_allergies: orNull(c.known_allergies),
        existing_conditions: orNull(c.existing_conditions),
        current_medications: orNull(c.current_medications),
        immunization_status: orNull(c.immunization_status),
        referred_by: orNull(c.referred_by),
      })),
    };

    this.loading.set(true);
    this.error.set(null);

    this.auth.register(payload).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.result.set(res);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(this.errorText(err));
      },
    });
  }

  private errorText(err: HttpErrorResponse): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: unknown[]; msg: string }) => `${(d.loc ?? []).slice(1).join(' > ')}: ${d.msg}`)
        .join('; ');
    }
    return err.status === 0
      ? 'Cannot reach the server. Is the backend running?'
      : 'Registration failed. Please try again.';
  }
}