export type Role = 'guardian' | 'doctor' | 'admin';

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

export interface DoctorTokenResponse extends AuthTokenResponse {
  must_change_password: boolean;
  doctor_name: string;
}

export interface GuardianProfile {
  guardian_id: number;
  first_name: string;
  last_name: string;
  mobile_number: string;
  role: string;
}

export interface DoctorProfile {
  doctor_id: number;
  staff_id: string;
  first_name: string;
  last_name: string;
  specialty: string;
  registration_no: string;
  must_change_password: boolean;
}
export interface ChildCreateRequest {
  first_name: string;
  last_name: string;
  date_of_birth: string; // YYYY-MM-DD
  gender: string;
  abha_id: string | null;
  aadhaar_number: string | null;
  blood_group: string | null;
  known_allergies: string | null;
  existing_conditions: string | null;
  current_medications: string | null;
  immunization_status: string | null;
  referred_by: string | null;
}

export interface RegistrationRequest {
  first_name: string;
  last_name: string;
  relationship_to_child: string;
  mobile_number: string;
  email: string | null;
  password: string;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string;
  pincode: string;
  preferred_language: string | null;
  terms_accepted: boolean;
  health_data_consent: boolean;
  children: ChildCreateRequest[];
}

export interface RegistrationResponse {
  guardian_id: number;
  patients: { patient_id: number; mrn: string; first_name: string }[];
  message: string;
}
export interface DoctorPublic {
  doctor_id: number;
  first_name: string;
  last_name: string;
  qualification: string;
  specialty: string;
  experience_years: number;
  languages: string | null;
  consultation_fee: number;
  available_days: string | null;
}

export interface SpecialtyCount {
  specialty: string;
  doctor_count: number;
}

export interface SlotsResponse {
  doctor_id: number;
  doctor_name: string;
  date: string;
  day_of_week: number;
  slots: string[]; // "HH:MM"
}

export interface PatientSummary {
  patient_id: number;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_group: string | null;
  guardian_name: string;
  guardian_mobile: string;
}

export interface Appointment {
  appointment_id: number;
  appointment_ref: string;
  doctor_id: number;
  doctor_name: string;
  patient_id: number;
  patient_name: string;
  mrn: string;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  reason_for_visit: string | null;
}

export interface BookingRequest {
  doctor_id: number;
  patient_id: number;
  scheduled_at: string; // "YYYY-MM-DDTHH:MM:00"
  reason_for_visit: string | null;
}
export interface Medication {
  medication_name: string;
  dosage: string | null;
  frequency: string | null;
  duration: string | null;
  instructions: string | null;
}

export interface TreatmentRecord {
  treatment_record_id: number;
  patient_id: number;
  patient_name: string;
  doctor_id: number;
  doctor_name: string;
  appointment_id: number | null;
  visit_date: string;
  diagnosis: string;
  medications: Medication[];
  treatment_plan: string | null;
  follow_up_date: string | null;
  clinical_notes: string | null;
  record_status: string;
  created_at: string;
}
export interface TreatmentRecordRequest {
  patient_id: number;
  appointment_id: number | null;
  visit_date: string;
  diagnosis: string;
  medications: Medication[];
  treatment_plan: string | null;
  follow_up_date: string | null;
  clinical_notes: string | null;
}
export interface DoctorSummary {
  doctor_id: number;
  staff_id: string;
  first_name: string;
  last_name: string;
  qualification: string;
  specialty: string;
  experience_years: number;
  languages: string | null;
  consultation_fee: number;
  available_days: string | null;
}

export interface DoctorCreateRequest {
  first_name: string;
  last_name: string;
  registration_no: string;
  qualification: string;
  specialty: string;
  experience_years: number;
  languages: string | null;
  consultation_fee: number;
  available_days: string | null;
  mobile_number: string | null;
  email: string | null;
  temporary_password: string;
}

export interface DoctorCreateResponse {
  doctor_id: number;
  staff_id: string;
  first_name: string;
  last_name: string;
  specialty: string;
  message: string;
}

export interface Availability {
  availability_id: number;
  doctor_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_minutes: number;
}

export interface AvailabilityRequest {
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_minutes: number;
}

export interface PageResult<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface UserRow {
  user_id: number;
  username: string;
  user_type: string;
  first_name: string | null;
  last_name: string | null;
  is_active?: boolean | null;
}

export interface UserCreateRequest {
  username: string;
  password: string;
  user_type: string;
  first_name: string | null;
  last_name: string | null;
}

export interface AssignmentResponse {
  message: string;
  patient_id: number;
  patient_name: string;
  doctor_id: number;
  doctor_name: string;
  assignment_date: string;
}