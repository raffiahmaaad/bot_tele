/**
 * API Client for BotStore Backend
 */

declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    // Load token from localStorage on init (client-side only)
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('access_token', token);
      } else {
        localStorage.removeItem('access_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return { error: data.error || 'Terjadi kesalahan' };
      }

      return { data };
    } catch (error) {
      console.error('API Error:', error);
      return { error: 'Tidak dapat terhubung ke server' };
    }
  }

  // ==================== AUTH ====================

  async register(email: string, password: string, name: string) {
    const result = await this.request<{ user: any; access_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });

    if (result.data?.access_token) {
      this.setToken(result.data.access_token);
    }

    return result;
  }

  async login(email: string, password: string) {
    const result = await this.request<{ user: any; access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (result.data?.access_token) {
      this.setToken(result.data.access_token);
    }

    return result;
  }

  async getMe() {
    return this.request<{ user: any }>('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // ==================== BOTS ====================

  async getBots() {
    return this.request<{ bots: any[] }>('/bots');
  }

  async createBot(telegramToken: string) {
    return this.request<{ bot: any }>('/bots', {
      method: 'POST',
      body: JSON.stringify({ telegram_token: telegramToken }),
    });
  }

  async getBot(botId: number) {
    return this.request<{ bot: any; stats: any }>(`/bots/${botId}`);
  }

  async updateBot(botId: number, data: any) {
    return this.request<{ bot: any }>(`/bots/${botId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteBot(botId: number) {
    return this.request<{ message: string }>(`/bots/${botId}`, {
      method: 'DELETE',
    });
  }

  // ==================== PRODUCTS ====================

  async getProducts(botId: number) {
    return this.request<{ products: any[] }>(`/bots/${botId}/products`);
  }

  async createProduct(botId: number, data: any) {
    return this.request<{ product: any }>(`/bots/${botId}/products`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async addProductStock(productId: number, stockItems: string[]) {
    return this.request<{ added_count: number }>(`/products/${productId}/stock`, {
      method: 'POST',
      body: JSON.stringify({ stock_items: stockItems }),
    });
  }

  // ==================== TRANSACTIONS ====================

  async getTransactions(botId: number) {
    return this.request<{ transactions: any[]; stats: any }>(`/bots/${botId}/transactions`);
  }

  // ==================== BROADCAST ====================

  async getBroadcasts(botId: number) {
    return this.request<{ broadcasts: any[] }>(`/bots/${botId}/broadcast`);
  }

  async sendBroadcast(botId: number, message: string) {
    return this.request<{ broadcast: any; message?: string }>(`/bots/${botId}/broadcast`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // ==================== SHEERID VERIFICATION ====================

  async getSheerIDTypes() {
    return this.request<{ types: SheerIDType[] }>('/sheerid/types');
  }

  async checkSheerIDLink(url: string, type: string) {
    return this.request<{ valid: boolean; error?: string; step?: string }>('/sheerid/check-link', {
      method: 'POST',
      body: JSON.stringify({ url, type }),
    });
  }

  async submitSheerIDVerification(url: string, type: string) {
    return this.request<SheerIDVerificationResult>('/sheerid/verify', {
      method: 'POST',
      body: JSON.stringify({ url, type }),
    });
  }

  async getSheerIDVerifications() {
    return this.request<{ verifications: SheerIDVerification[] }>('/sheerid/verifications');
  }

  async getSheerIDVerification(id: number) {
    return this.request<{ verification: SheerIDVerification }>(`/sheerid/verifications/${id}`);
  }

  async getSheerIDSettings() {
    return this.request<{ settings: SheerIDSettings }>('/sheerid/settings');
  }

  async saveSheerIDSettings(settings: Partial<SheerIDSettings>) {
    return this.request<{ message: string; settings: SheerIDSettings }>('/sheerid/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async ipLookup() {
    return this.request<IPLookupResult>('/sheerid/ip-lookup');
  }

  async proxyCheck(host: string, port: number, username?: string, password?: string) {
    return this.request<ProxyCheckResult>('/sheerid/proxy-check', {
      method: 'POST',
      body: JSON.stringify({ host, port, username, password }),
    });
  }

  async checkVerificationStatus(verificationId: number) {
    return this.request<VerificationStatusResult>(`/sheerid/verifications/${verificationId}/status`);
  }
}

// Verification Status Result (real-time from SheerID)
export interface VerificationStatusResult {
  success: boolean;
  approved?: boolean;
  status?: string;
  status_display?: string;
  message?: string;
  redirect_url?: string;
  claim_url?: string;
  credits?: number;
  verify_type?: string;
  verification_id?: number;
  error?: string;
}

// IP Lookup Result
export interface IPLookupResult {
  success: boolean;
  ip?: string;
  city?: string;
  region?: string;
  country?: string;
  country_code?: string;
  isp?: string;
  timezone?: string;
  source?: string;
  error?: string;
}

// Proxy Check Result
export interface ProxyCheckResult {
  success: boolean;
  valid?: boolean;
  ip?: string;
  city?: string;
  region?: string;
  country?: string;
  country_code?: string;
  isp?: string;
  timezone?: string;
  message?: string;
  error?: string;
}

// SheerID Types
export interface SheerIDType {
  id: string;
  name: string;
  cost: number;
  icon: string;
}

export interface SheerIDVerification {
  id: number;
  verify_type: string;
  verify_url: string;
  verify_id: string;
  status: string;
  result_message?: string;
  student_name?: string;
  student_email?: string;
  school_name?: string;
  redirect_url?: string;
  points_cost: number;
  created_at: string;
  processed_at?: string;
  error_details?: string;
}

export interface SheerIDVerificationResult {
  success: boolean;
  message?: string;
  error?: string;
  verification_id: number;
  student_name?: string;
  student_email?: string;
  school_name?: string;
  redirect_url?: string;
  points_cost?: number;
}

export interface SheerIDSettings {
  proxy_enabled: boolean;
  proxy_host?: string;
  proxy_port?: number;
  proxy_username?: string;
  proxy_password?: string;
  default_points_cost: number;
}

// Singleton instance
export const api = new ApiClient();
export default api;
