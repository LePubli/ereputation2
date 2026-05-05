export interface Prospect {
  id: string;
  siren: string;
  siret?: string;
  raisonSociale: string;
  adresse?: string;
  codeNaf?: string;
  effectifs?: number;
  ca?: number;
  siteWeb?: string;
  email?: string;
  telephone?: string;
  stage: 'nouveau' | 'contacte' | 'rdv_pris' | 'negociation' | 'gagne' | 'perdu';
  scoreDigital?: number;
  createdAt: string;
  updatedAt: string;
}

export interface DigitalAudit {
  id: string;
  prospectId: string;
  cmsDetected?: string;
  hasHttps: boolean;
  pixels: string[];
  performanceScore?: number;
  seoScore?: number;
  socialMedia: {
    linkedin?: string;
    facebook?: string;
    twitter?: string;
    instagram?: string;
  };
  emailMarketing?: {
    spf: boolean;
    dkim: boolean;
    dmarc: boolean;
    platform?: string;
  };
  chatTools?: string[];
  overallScore: number;
  createdAt: string;
}

export interface PainPoint {
  id: string;
  prospectId: string;
  category: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  facts: string[];
  recommendedAction: string;
  createdAt: string;
}

export interface Interaction {
  id: string;
  prospectId: string;
  type: 'call' | 'email' | 'linkedin' | 'whatsapp' | 'note' | 'meeting';
  content: string;
  date: string;
  userId: string;
}

export interface PipelineStage {
  id: string;
  label: string;
  color: string;
  count: number;
}

export interface Plugin {
  name: string;
  version: string;
  description: string;
  author: string;
  active: boolean;
  dependencies: string[];
  endpoints: Array<{
    path: string;
    method: string;
    description: string;
  }>;
}

export interface Metrics {
  totalProspects: number;
  byStage: Record<string, number>;
  conversionRate: number;
  avgTimePerStage: Record<string, number>;
  revenueForecast: number;
}
