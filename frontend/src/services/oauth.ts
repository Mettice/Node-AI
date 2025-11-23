/**
 * OAuth-related API services
 */

import { apiClient } from '@/utils/api';

export interface OAuthInitRequest {
  service: string;
  client_id: string;
  redirect_uri: string;
  scopes: string[];
  user_id?: string;
  additional_params?: Record<string, string>;
}

export interface OAuthInitResponse {
  authorization_url: string;
  state: string;
}

export interface OAuthExchangeRequest {
  service: string;
  code: string;
  state: string;
  client_id: string;
  client_secret: string;
  redirect_uri: string;
  user_id?: string;
}

export interface OAuthExchangeResponse {
  success: boolean;
  token_id?: string;
  message?: string;
}

export interface OAuthToken {
  token_id: string;
  service: string;
  user_id?: string;
  created_at?: string;
  expires_at?: string;
  is_valid: boolean;
}

/**
 * Initialize OAuth flow and get authorization URL
 */
export async function initOAuthFlow(request: OAuthInitRequest): Promise<OAuthInitResponse> {
  const response = await apiClient.post<OAuthInitResponse>('/oauth/init', request);
  return response.data;
}

/**
 * Exchange OAuth authorization code for access token
 */
export async function exchangeOAuthCode(request: OAuthExchangeRequest): Promise<OAuthExchangeResponse> {
  const response = await apiClient.post<OAuthExchangeResponse>('/oauth/exchange', request);
  return response.data;
}

/**
 * List OAuth tokens
 */
export async function listOAuthTokens(service?: string, user_id?: string): Promise<OAuthToken[]> {
  const params = new URLSearchParams();
  if (service) params.append('service', service);
  if (user_id) params.append('user_id', user_id);
  
  const response = await apiClient.get<{ tokens: OAuthToken[] }>(`/oauth/tokens?${params.toString()}`);
  return response.data.tokens;
}

/**
 * Delete OAuth token
 */
export async function deleteOAuthToken(token_id: string): Promise<void> {
  await apiClient.delete(`/oauth/tokens/${token_id}`);
}

