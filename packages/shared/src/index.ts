/**
 * RankForge AI — Shared Types, Constants & Design Tokens
 */

export type FeatureState = 'available' | 'not_configured' | 'coming_soon' | 'failed';

export type OrganizationRole = 'owner' | 'admin' | 'member';

export type PlanTier = 'starter' | 'professional' | 'agency';

export type VerificationMethod = 'dns_txt' | 'meta_tag' | 'file_upload';

export type VerificationStatus = 'pending' | 'verified' | 'failed';

export type AuditJobStatus = 'pending' | 'running' | 'completed' | 'failed';

export type AuditJobType = 'preflight' | 'technical_crawl' | 'deep_inspection';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_tier: PlanTier;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: OrganizationRole;
  created_at: string;
  updated_at: string;
}

export interface WebsiteProject {
  id: string;
  organization_id: string;
  name: string;
  domain: string;
  primary_url: string;
  is_verified: boolean;
  verification_token: string;
  created_at: string;
  updated_at: string;
}

export interface AuditJob {
  id: string;
  project_id: string;
  organization_id: string;
  job_type: AuditJobType;
  status: AuditJobStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AuditResult {
  id: string;
  job_id: string;
  project_id: string;
  url: string;
  status_code: number;
  response_time_ms: number;
  headers_json: Record<string, string>;
  ssl_info_json: Record<string, unknown>;
  robots_txt_found: boolean;
  sitemap_found: boolean;
  issues_json: Array<{
    code: string;
    severity: 'critical' | 'warning' | 'info';
    title: string;
    description: string;
  }>;
  score: number;
  created_at: string;
}

export const BRAND = {
  name: 'RankForge AI',
  compactName: 'RankForge',
  tagline: 'Search intelligence. Engineered for growth.',
  description:
    'RankForge AI is a multi-tenant SEO intelligence and automation platform that enables businesses, website owners, and agencies to analyze technical SEO, discover optimization opportunities, track organic search performance, and safely apply approved improvements.',
} as const;

export const COLOR_TOKENS = {
  bgPrimary: '#111215',
  bgSecondary: '#191A1E',
  surfaceElevated: '#202126',
  crimsonPrimary: '#9F1733',
  crimsonHover: '#B51D3E',
  crimsonMuted: '#6D2233',
  borderSubtle: '#34353A',
  textPrimary: '#E9E9EC',
  textSecondary: '#92939A',
  textMuted: '#696A72',
  statusGreen: '#2E7D32',
  statusAmber: '#C57B14',
  statusRed: '#D32F2F',
} as const;
