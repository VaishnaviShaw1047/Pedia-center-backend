import { Routes } from '@angular/router';
import { passwordChangedGuard, roleGuard } from './core/role.guard';

const home = () => import('./shell/home').then((m) => m.Home);

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: 'login', loadComponent: () => import('./auth/login/login').then((m) => m.Login) },
  { path: 'register', loadComponent: () => import('./auth/register/register').then((m) => m.Register) },

  {
    path: 'guardian',
    canActivate: [roleGuard('guardian')],
    loadComponent: () => import('./parent/parent-layout').then((m) => m.ParentLayout),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'find-doctor' },
      { path: 'find-doctor', loadComponent: () => import('./parent/find-doctor').then((m) => m.FindDoctors) },
      { path: 'book/:doctorId', loadComponent: () => import('./parent/book-appointment').then((m) => m.BookAppointment) },
      { path: 'my-appointments', loadComponent: () => import('./parent/my-appointments').then((m) => m.MyAppointments) },
      { path: 'treatment-history', loadComponent: () => import('./parent/treatment-history').then((m) => m.TreatmentHistory) },
    ],
  },

  {
    path: 'doctor',
    canActivate: [roleGuard('doctor')],
    loadComponent: () => import('./doctors/doctor-layout').then((m) => m.DoctorLayout),
    children: [
      { path: 'change-password', loadComponent: () => import('./doctors/change-password').then((m) => m.ChangePassword) },
      {
        path: '',
        canActivate: [passwordChangedGuard],
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'schedule' },
          { path: 'schedule', loadComponent: () => import('./doctors/schedule').then((m) => m.Schedule) },
          { path: 'patients', loadComponent: () => import('./doctors/my-patients').then((m) => m.MyPatients) },
          { path: 'patients/:patientId', loadComponent: () => import('./doctors/patient-history').then((m) => m.PatientHistory) },
          { path: 'patients/:patientId/add-record', loadComponent: () => import('./doctors/add-record').then((m) => m.AddRecord) },
        ],
      },
    ],
  },

    {
    path: 'admin',
    canActivate: [roleGuard('admin')],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'doctors' },
      {
        path: 'doctors',
        loadComponent: () => import('./admin/manage-doctors').then((m) => m.ManageDoctors),
      },
      {
        path: 'doctors/new',
        loadComponent: () => import('./admin/add-doctor').then((m) => m.AddDoctor),
      },
      {
        path: 'doctors/:doctorId/availability',
        redirectTo: '/admin/doctors',
      },
      {
        path: 'patients',
        loadComponent: () => import('./admin/manage-patients').then((m) => m.ManagePatients),
      },
      {
        path: 'users',
        loadComponent: () => import('./admin/manage-users').then((m) => m.ManageUsers),
      },
    ],
  },
  { path: '**', redirectTo: 'login' },
];