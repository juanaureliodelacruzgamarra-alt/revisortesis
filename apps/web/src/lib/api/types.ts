export type ProgramLevel = "undergraduate" | "masters" | "doctorate";

export const PROGRAM_LEVEL_LABELS: Record<ProgramLevel, string> = {
  undergraduate: "Pregrado",
  masters: "Maestría",
  doctorate: "Doctorado",
};

export type Program = {
  id: string;
  name: string;
  code: string;
  level: ProgramLevel;
  created_at: string;
};

export type TemplateParsingStatus =
  | "pending"
  | "processing"
  | "parsed"
  | "failed";

export const TEMPLATE_STATUS_LABELS: Record<TemplateParsingStatus, string> = {
  pending: "Pendiente",
  processing: "Procesando",
  parsed: "Procesado",
  failed: "Fallido",
};

export type TemplateSection = {
  number: string | null;
  title: string;
  canonical_title: string;
  level: number;
  char_count: number;
  paragraph_count: number;
  children: TemplateSection[];
};

export type TemplateStructure = {
  sections: TemplateSection[];
  total_paragraphs: number;
  total_chars: number;
  page_count: number;
};

export type TemplateSummary = {
  id: string;
  program_id: string;
  title: string;
  version: number;
  description: string | null;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  parsing_status: TemplateParsingStatus;
  parsing_error: string | null;
  is_active: boolean;
  created_at: string;
};

export type TemplateDetail = TemplateSummary & {
  structure_json: TemplateStructure | null;
  rubric_json: Record<string, unknown> | null;
  program: Program;
};

// ---- Submissions ----

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

export type SubmissionStudent = {
  id: string;
  email: string;
  full_name: string;
};

export type SubmissionVersionSummary = {
  id: string;
  version_number: number;
  comment: string | null;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  parsing_status: VersionParsingStatus;
  parsing_error: string | null;
  created_at: string;
};

export type SubmissionVersionDetail = SubmissionVersionSummary & {
  structure_json: TemplateStructure | null;
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

export type SubmissionDetail = SubmissionSummary & {
  versions: SubmissionVersionSummary[];
};

// ---- AI evaluation ----

export type FindingSeverity = "critical" | "major" | "minor" | "suggestion";

export const SEVERITY_LABELS: Record<FindingSeverity, string> = {
  critical: "Crítico",
  major: "Mayor",
  minor: "Menor",
  suggestion: "Sugerencia",
};

export type FindingType =
  | "missing_section"
  | "structural_error"
  | "content_error"
  | "form_error"
  | "coherence_issue"
  | "suggestion";

export const FINDING_TYPE_LABELS: Record<FindingType, string> = {
  missing_section: "Sección faltante",
  structural_error: "Error estructural",
  content_error: "Error de contenido",
  form_error: "Error de forma",
  coherence_issue: "Incoherencia",
  suggestion: "Sugerencia",
};

export type HumanAction = "accepted" | "modified" | "rejected";

export const HUMAN_ACTION_LABELS: Record<HumanAction, string> = {
  accepted: "Aceptado",
  modified: "Modificado",
  rejected: "Descartado",
};

export type AIFinding = {
  id: string;
  section: string | null;
  page_approx: number | null;
  type: FindingType;
  severity: FindingSeverity;
  description: string;
  instruction: string;
  example: string;
  recommendation: string;
  human_action: HumanAction | null;
  human_comment: string | null;
  human_severity_override: FindingSeverity | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type AIEvaluation = {
  id: string;
  version_id: string;
  backend: string;
  model: string;
  prompt_version: string;
  duration_ms: number;
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

// ---- Plagiarism ----

export type PlagiarismSource = "intra" | "copyleaks";
export type PlagiarismStatus = "pending" | "confirmed" | "dismissed";

export type ChunkPreview = {
  id: string;
  chunk_index: number;
  section: string | null;
  text: string;
  char_count: number;
};

export type PlagiarismMatch = {
  id: string;
  similarity: number;
  source: PlagiarismSource;
  status: PlagiarismStatus;
  created_at: string;
  matched_version_id: string;
  matched_student_name: string;
  matched_submission_title: string;
  source_chunk: ChunkPreview;
  matched_chunk: ChunkPreview;
};

// ---- Citations ----

export type CitationStatus =
  | "pending"
  | "verified"
  | "partial"
  | "not_found"
  | "hallucinated";

export const CITATION_STATUS_LABELS: Record<CitationStatus, string> = {
  pending: "Pendiente",
  verified: "Verificada",
  partial: "Parcial",
  not_found: "No encontrada",
  hallucinated: "Posible invento",
};

export type Citation = {
  id: string;
  raw_text: string;
  title: string | null;
  authors: string | null;
  year: number | null;
  journal: string | null;
  doi: string | null;
  crossref_status: CitationStatus;
  crossref_message: string | null;
  checked_at: string | null;
  created_at: string;
};

// ---- ORCID ----

export type OrcidAuthorize = {
  authorize_url: string;
  state: string;
  mode: "real" | "stub";
};

export type OrcidStatus = {
  linked: boolean;
  orcid_id: string | null;
  affiliation: string | null;
  last_sync: string | null;
  publications_count: number;
};

export type OrcidPublication = {
  id: string;
  put_code: string;
  title: string;
  year: number | null;
  journal: string | null;
  doi: string | null;
  url: string | null;
  created_at: string;
};

export type OrcidLinkResult = OrcidStatus & {
  backend: string;
};
