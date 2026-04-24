export type RequirementStatus = "satisfied" | "partially_satisfied" | "not_satisfied" | "unclear";
export type RequirementType = "eligibility" | "required_document" | "budget" | "narrative" | "compliance";
export type RequirementImportance = "required" | "preferred" | "optional";
export type RiskSeverity = "high" | "medium" | "low";
export type ProjectStatus = "draft" | "documents_uploaded" | "analyzing" | "analyzed" | "report_generated" | "error";

export interface Citation {
  document_name: string;
  page_number: number;
  summary: string;
}

export interface Requirement {
  id: string;
  text: string;
  type: RequirementType;
  importance: RequirementImportance;
  status: RequirementStatus;
  confidence: number;
  evidence: Citation[];
}

export interface MissingDocument {
  name: string;
  required: boolean;
  description: string;
}

export interface RiskFlag {
  severity: RiskSeverity;
  title: string;
  description: string;
}

export interface DraftAnswer {
  id: string;
  question: string;
  draft_answer: string;
  citations: Citation[];
  missing_evidence: string[];
  confidence: number;
}

export interface Organization {
  id: string;
  name: string;
  mission: string;
  location: string;
  nonprofit_type: string;
  annual_budget: number;
  population_served: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  grant_name: string;
  grant_source_url: string | null;
  /** Optional — supplied at project creation or via demo seed */
  funder_name: string | null;
  grant_amount: string | null;
  deadline: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export type DocumentType =
  | "mission_statement"
  | "budget"
  | "annual_report"
  | "program_description"
  | "irs_letter"
  | "past_application"
  | "grant_opportunity"
  | "other";

export type DocumentStatus = "uploaded" | "stored" | "parsed" | "parse_failed";

export interface Document {
  id: string;
  organization_id: string;
  project_id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  page_count: number | null;
  created_at: string;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
}

export interface OrganizationCreate {
  name: string;
  mission: string;
  location: string;
  nonprofit_type: string;
  annual_budget: number;
  population_served: string;
}

export interface ProjectCreate {
  organization_id: string;
  grant_name: string;
  grant_source_url?: string | null;
  funder_name?: string | null;
  grant_amount?: string | null;
  deadline?: string | null;
}

/** Returned by GET /projects/{id}/analysis */
export interface AnalysisResult {
  project_id: string;
  eligibility_score: number;
  readiness_score: number;
  requirements: Requirement[];
  missing_documents: MissingDocument[];
  risk_flags: RiskFlag[];
  draft_answers: DraftAnswer[];
}
