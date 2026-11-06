import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AdminApi } from '../core/admin-api.service';
import { errorMessage } from '../core/error-message';
import { UserRow } from '../core/models';

@Component({
  selector: 'app-manage-users',
  imports: [ReactiveFormsModule],
  template: `
    <div class="head">
      <h1>Users</h1>
      <button type="button" class="primary" (click)="showForm.set(!showForm())">
        {{ showForm() ? 'Close' : '+ Add user' }}
      </button>
    </div>

    @if (showForm()) {
      <form class="card" [formGroup]="form" (ngSubmit)="create()">
        <div class="grid">
          <label>Username <input formControlName="username" /></label>
          <label>Password (min 8) <input type="password" formControlName="password" /></label>
          <label>
            Type
            <select formControlName="user_type">
              <option value="Admin">Admin</option>
              <option value="Staff">Staff</option>
            </select>
          </label>
          <label>First name <input formControlName="first_name" /></label>
          <label>Last name <input formControlName="last_name" /></label>
        </div>
        <p class="muted">Only users of type Admin can sign in on the Admin tab.</p>
        <button class="primary" type="submit" [disabled]="form.invalid || saving()">
          {{ saving() ? 'Saving…' : 'Create user' }}
        </button>
      </form>
    }

    <div class="searchbar">
      <input #q type="search" placeholder="Search by name or username" (keyup.enter)="search(q.value)" />
      <button type="button" class="secondary" (click)="search(q.value)">Search</button>
    </div>

    @if (error()) { <p class="err">{{ error() }}</p> }
    @if (message()) { <p class="ok">{{ message() }}</p> }

    @if (loading()) {
      <p class="muted">Loading…</p>
    } @else {
      <p class="muted">{{ total() }} user(s) · page {{ page() }} of {{ totalPages() }}</p>
      <div class="list">
        @for (u of users(); track u.user_id) {
          <article class="card row">
            <div>
              <h2>{{ u.username }} <span class="badge">{{ u.user_type }}</span></h2>
              <p class="muted">{{ u.first_name }} {{ u.last_name }}</p>
            </div>

            @if (resetting() === u.user_id) {
              <div class="reset">
                <input #pw type="password" placeholder="New password (min 8)" />
                <button type="button" class="primary" [disabled]="pw.value.length < 8" (click)="reset(u, pw.value)">
                  Reset
                </button>
                <button type="button" class="secondary" (click)="resetting.set(null)">Cancel</button>
              </div>
            } @else {
              <button type="button" class="secondary" (click)="resetting.set(u.user_id)">Reset password</button>
            }
          </article>
        } @empty {
          <div class="card"><p class="muted">No users found.</p></div>
        }
      </div>

      <div class="pager">
        <button type="button" class="secondary" [disabled]="page() <= 1" (click)="go(page() - 1)">Previous</button>
        <button type="button" class="secondary" [disabled]="page() >= totalPages()" (click)="go(page() + 1)">Next</button>
      </div>
    }
  `,
  styles: `
    .head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    h1 { margin: 0; color: #4b3a8a; }
    .card { margin-bottom: .75rem; padding: 1rem 1.25rem; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / 6%); }
    .row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
    .row h2 { margin: 0; font-size: 1.05rem; }
    .row p { margin: .2rem 0; font-size: .9rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: .75rem 1rem; }
    label { display: block; font-size: .9rem; }
    input, select { width: 100%; box-sizing: border-box; margin-top: .25rem; padding: .55rem; border: 1px solid #d6d0ea; border-radius: 8px; background: #fff; }
    .searchbar { display: flex; gap: .5rem; margin: 1rem 0 .75rem; }
    .searchbar input { margin: 0; }
    .reset { display: flex; gap: .5rem; flex-wrap: wrap; align-items: center; }
    .reset input { margin: 0; width: 200px; }
    .primary { padding: .5rem 1rem; border: 0; border-radius: 8px; background: #4b3a8a; color: #fff; cursor: pointer; margin-top: .5rem; }
    .head .primary, .reset .primary { margin-top: 0; }
    .primary:disabled { opacity: .5; cursor: not-allowed; }
    .secondary { padding: .5rem 1rem; border: 1px solid #4b3a8a; background: #fff; color: #4b3a8a; border-radius: 8px; cursor: pointer; }
    .secondary:disabled { opacity: .5; cursor: not-allowed; }
    .badge { margin-left: .4rem; padding: .15rem .6rem; border-radius: 999px; font-size: .75rem; background: #ece8f7; color: #4b3a8a; }
    .pager { display: flex; justify-content: center; gap: .75rem; margin-top: 1rem; }
    .muted { color: #6b6785; font-size: .9rem; }
    .err { color: #b3261e; }
    .ok { color: #1b7f3b; }
    @media (max-width: 700px) { .row { flex-direction: column; align-items: flex-start; } }
  `,
})
export class ManageUsers implements OnInit {
  private fb = inject(NonNullableFormBuilder);
  private api = inject(AdminApi);
  private pageSize = 10;
  private query = '';

  users = signal<UserRow[]>([]);
  page = signal(1);
  total = signal(0);
  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));

  loading = signal(false);
  saving = signal(false);
  showForm = signal(false);
  resetting = signal<number | null>(null);
  error = signal<string | null>(null);
  message = signal<string | null>(null);

  form = this.fb.group({
    username: ['', [Validators.required, Validators.maxLength(50)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    user_type: ['Admin', Validators.required],
    first_name: [''],
    last_name: [''],
  });

  ngOnInit() {
    this.load();
  }

  search(q: string) {
    this.query = q;
    this.page.set(1);
    this.load();
  }

  go(page: number) {
    this.page.set(page);
    this.load();
  }

  private load() {
    this.loading.set(true);
    this.error.set(null);
    this.api.users(this.query, this.page(), this.pageSize).subscribe({
      next: (res) => {
        this.users.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(errorMessage(e, 'Could not load users.'));
      },
    });
  }

  create() {
    if (this.form.invalid) return;
    const v = this.form.getRawValue();
    const orNull = (s: string) => (s.trim() ? s.trim() : null);

    this.saving.set(true);
    this.error.set(null);
    this.message.set(null);

    this.api
      .createUser({
        username: v.username.trim(),
        password: v.password,
        user_type: v.user_type,
        first_name: orNull(v.first_name),
        last_name: orNull(v.last_name),
      })
      .subscribe({
        next: (u) => {
          this.saving.set(false);
          this.message.set(`User ${u.username} created.`);
          this.form.reset({ user_type: 'Admin' });
          this.showForm.set(false);
          this.load();
        },
        error: (e: HttpErrorResponse) => {
          this.saving.set(false);
          this.error.set(errorMessage(e, 'Could not create the user.'));
        },
      });
  }

  reset(user: UserRow, newPassword: string) {
    this.error.set(null);
    this.message.set(null);
    this.api.resetPassword(user.user_id, newPassword).subscribe({
      next: () => {
        this.resetting.set(null);
        this.message.set(`Password reset for ${user.username}.`);
      },
      error: (e: HttpErrorResponse) => this.error.set(errorMessage(e, 'Could not reset the password.')),
    });
  }
}