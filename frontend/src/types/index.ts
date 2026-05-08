// Types TypeScript Phase 2

export interface Contact {
  id: string; prospect_id: string;
  first_name: string | null; last_name: string | null; role: string | null;
  email: string | null; phone: string | null; linkedin_url: string | null;
  is_primary: boolean; created_at: string; updated_at: string;
}

export interface Prospect {
  id: string; company_name: string; siren: string | null; siret: string | null;
  legal_form: string | null; naf_code: string | null; naf_label: string | null;
  creation_date: string | null; employee_range: string | null; capital: number | null;
  address: string | null; postal_code: string | null; city: string | null;
  department: string | null; region: string | null; country: string;
  latitude: number | null; longitude: number | null;
  website: string | null; phone: string | null; email: string | null;
  stage_id: string | null; stage_position: number;
  digital_score: number | null; propensity_score: number | null;
  propensity_category: 'HOT' | 'WARM' | 'COLD' | null;
  enrichment: Record<string, unknown>; sources_used: string[];
  last_enriched_at: string | null; notes: string | null; tags: string[];
  estimated_revenue: number | null; consent_given: boolean; opt_out: boolean;
  source: string; activities_count: number; last_activity_at: string | null;
  scoring_details: Record<string, unknown>;
  created_at: string; updated_at: string; contacts: Contact[];
}

export interface ProspectListResponse {
  items: Prospect[]; total: number; page: number; page_size: number;
}
export interface ProspectImportResult {
  imported: number; skipped: number; errors: string[];
}

// Pipeline
export interface PipelineStage {
  id: string; name: string; slug: string; description: string | null;
  color: string; order: number; is_won: boolean; is_lost: boolean;
  is_active: boolean; created_at: string; updated_at: string;
}
export interface KanbanCard {
  id: string; company_name: string; siren: string | null; city: string | null;
  propensity_category: 'HOT' | 'WARM' | 'COLD' | null; propensity_score: number | null;
  digital_score: number | null; estimated_revenue: number | null;
  stage_position: number; tags: string[]; activities_count?: number;
}
export interface KanbanColumn { stage: PipelineStage; cards: KanbanCard[]; count: number; }
export interface KanbanBoard { columns: KanbanColumn[]; total: number; }

// Dashboard
export interface DashboardKPI {
  total_prospects: number; conversion_rate: number;
  estimated_revenue: number; active_plugins: number;
}
export interface StageDistribution { stage_id: string; stage_name: string; color: string; count: number; }
export interface DashboardStats { kpi: DashboardKPI; distribution: StageDistribution[]; last_updated: string; }
export interface SystemInfo {
  app_name: string; app_version: string; status: string;
  uptime_seconds: number; plugins_count: number; plugins_active: string[];
  database: string; redis: string;
}
export interface PluginInfo { name: string; version: string; description: string | null; active: boolean; config: Record<string, unknown>; }
export interface PluginsResponse { plugins: PluginInfo[]; total: number; active_count: number; }

// Auth
export interface AuthUser { id: string; email: string; full_name: string; role: string; }
export interface TokenResponse { access_token: string; refresh_token: string; token_type: string; expires_in: number; }

// Activities
export type ActivityType = 'call' | 'email' | 'meeting' | 'note' | 'task' | 'linkedin' | 'other';
export type ActivityOutcome = 'positive' | 'neutral' | 'negative';

export interface Activity {
  id: string; prospect_id: string; user_id: string | null;
  type: ActivityType; title: string; body: string | null;
  outcome: ActivityOutcome | null; scheduled_at: string | null;
  completed_at: string | null; is_completed: boolean;
  created_at: string; updated_at: string;
}

// Filtres
export interface ProspectFilters {
  search?: string; stage_id?: string; naf_code?: string;
  region?: string; department?: string;
  propensity_category?: 'HOT' | 'WARM' | 'COLD';
  source?: string; has_website?: boolean; has_phone?: boolean;
  min_score?: number; tags?: string;
  sort_by?: string; sort_dir?: 'asc' | 'desc';
}
