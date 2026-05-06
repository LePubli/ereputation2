// Types TypeScript du domaine

export interface Contact {
  id: string;
  prospect_id: string;
  first_name: string | null;
  last_name: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface Prospect {
  id: string;
  company_name: string;
  siren: string | null;
  siret: string | null;
  legal_form: string | null;
  naf_code: string | null;
  naf_label: string | null;
  creation_date: string | null;
  employee_range: string | null;
  capital: number | null;

  address: string | null;
  postal_code: string | null;
  city: string | null;
  department: string | null;
  region: string | null;
  country: string;
  latitude: number | null;
  longitude: number | null;

  website: string | null;
  phone: string | null;
  email: string | null;

  stage_id: string | null;
  stage_position: number;
  digital_score: number | null;
  propensity_score: number | null;
  propensity_category: 'HOT' | 'WARM' | 'COLD' | null;

  enrichment: Record<string, unknown>;
  sources_used: string[];
  last_enriched_at: string | null;

  notes: string | null;
  tags: string[];

  estimated_revenue: number | null;
  consent_given: boolean;
  opt_out: boolean;

  created_at: string;
  updated_at: string;
  contacts: Contact[];
}

export interface ProspectListResponse {
  items: Prospect[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProspectImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export interface PipelineStage {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  color: string;
  order: number;
  is_won: boolean;
  is_lost: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KanbanCard {
  id: string;
  company_name: string;
  siren: string | null;
  city: string | null;
  propensity_category: 'HOT' | 'WARM' | 'COLD' | null;
  propensity_score: number | null;
  digital_score: number | null;
  estimated_revenue: number | null;
  stage_position: number;
  tags: string[];
}

export interface KanbanColumn {
  stage: PipelineStage;
  cards: KanbanCard[];
  count: number;
}

export interface KanbanBoard {
  columns: KanbanColumn[];
  total: number;
}

export interface DashboardKPI {
  total_prospects: number;
  conversion_rate: number;
  estimated_revenue: number;
  active_plugins: number;
}

export interface StageDistribution {
  stage_id: string;
  stage_name: string;
  color: string;
  count: number;
}

export interface DashboardStats {
  kpi: DashboardKPI;
  distribution: StageDistribution[];
  last_updated: string;
}

export interface SystemInfo {
  app_name: string;
  app_version: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;
  plugins_count: number;
  plugins_active: string[];
  database: 'ok' | 'error';
  redis: 'ok' | 'error';
}

export interface PluginInfo {
  name: string;
  version: string;
  description: string | null;
  active: boolean;
  config: Record<string, unknown>;
}

export interface PluginsResponse {
  plugins: PluginInfo[];
  total: number;
  active_count: number;
}
