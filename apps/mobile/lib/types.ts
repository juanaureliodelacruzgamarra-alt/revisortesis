export type UserRole = "student" | "advisor" | "coordinator" | "admin";

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type SubmissionStatus =
  | "draft"
  | "in_progress"
  | "observed"
  | "approved"
  | "rejected";

export const SUBMISSION_STATUS_LABELS: Record<SubmissionStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  observed: "Observado",
  approved: "Aprobado",
  rejected: "Rechazado",
};

export type VersionParsingStatus =
  | "pending"
  | "processing"
  | "parsed"
  | "failed"
  | "ai_queued"
  | "ai_processing"
  | "ai_completed";

export const VERSION_STATUS_LABELS: Record<VersionParsingStatus, string> = {
  pending: "Pendiente",
  processing: "Procesando",
  parsed: "Procesado",
  failed: "Fallido",
  ai_queued: "En cola IA",
  ai_processing: "Análisis IA",
  ai_completed: "Análisis completado",
};

export type Program = {
  id: string;
  name: string;
  code: string;
};

export type SubmissionStudent = {
  id: string;
  email: string;
  full_name: string;
};

export type SubmissionSummary = {
  id: string;
  title: string;
  chapter: string | null;
  status: SubmissionStatus;
  program_id: string;
  template_id: string | null;
  advisor_id: string | null;
  student: SubmissionStudent;
  program: Program;
  created_at: string;
  latest_version_number: number | null;
  latest_version_status: VersionParsingStatus | null;
  advisor_fit_score: number | null;
  advisor_fit_alert: boolean;
};

export type SubmissionVersionSummary = {
  id: string;
  version_number: number;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  parsing_status: VersionParsingStatus;
  parsing_error: string | null;
  created_at: string;
};

export type SubmissionDetail = SubmissionSummary & {
  versions: SubmissionVersionSummary[];
};

export type FindingSeverity = "critical" | "major" | "minor" | "suggestion";
export const SEVERITY_LABELS: Record<FindingSeverity, string> = {
  critical: "Crítico",
  major: "Mayor",
  minor: "Menor",
  suggestion: "Sugerencia",
};

export type AIFinding = {
  id: string;
  section: string | null;
  type: string;
  severity: FindingSeverity;
  description: string;
  instruction: string;
  example: string;
  recommendation: string;
  human_action: string | null;
  human_severity_override: FindingSeverity | null;
};

export type AIEvaluation = {
  id: string;
  version_id: string;
  backend: string;
  model: string;
  structure_score: number;
  content_score: number;
  form_score: number;
  originality_score: number;
  total_percentage: number;
  decimal_grade: number;
  executive_summary: string;
  created_at: string;
  findings: AIFinding[];
};
