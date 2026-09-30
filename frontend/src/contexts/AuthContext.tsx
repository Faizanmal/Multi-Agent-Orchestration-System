"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { jwtDecode } from 'jwt-decode';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthProvider {
  id: string;
  provider: 'email' | 'google' | 'github' | 'firebase';
  email?: string;
  display_name?: string;
  avatar_url?: string;
  created_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  display_name?: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
  subscription_tier: 'free' | 'pro' | 'enterprise';
  is_email_verified?: boolean;
  date_joined: string;
  providers?: AuthProvider[];
}

export interface Session {
  id: string;
  session_id: string | null;
  provider: string;
  device_name: string;
  device_type: string;
  browser: string;
  os: string;
  ip_address: string | null;
  created_at: string;
  last_used_at: string | null;
  expires_at: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface RegisterData {
  username?: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  loginWithGoogle: () => Promise<boolean>;
  loginWithGitHub: () => Promise<boolean>;
  loginWithFirebase: (idToken: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshTokens: () => Promise<boolean>;
  updateProfile: (data: Partial<User>) => Promise<boolean>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
  resetPassword: (email: string) => Promise<boolean>;
  linkGoogle: () => Promise<string | null>;
  linkGitHub: () => Promise<string | null>;
  unlinkGoogle: () => Promise<boolean>;
  unlinkGitHub: () => Promise<boolean>;
  getSessions: () => Promise<Session[]>;
  revokeSession: (sessionId: string) => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  handleOAuthCallback: (access: string, refresh: string) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Prefer 127.0.0.1 over localhost — Django runserver binds IPv4 only;
// Windows localhost→::1 can hang and leave the dashboard spinner stuck.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const AUTH_BASE = `${API_BASE}/api/auth`;
const AUTH_FETCH_TIMEOUT_MS = 20_000;

const TOKEN_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function storeTokens(access: string, refresh?: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem('auth_token', access); // legacy api client key
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

function clearTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  // Clear legacy token keys used by older clients
  localStorage.removeItem('auth_token');
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
}

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredRefresh(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}

function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<{ exp: number }>(token);
    return (decoded.exp || 0) * 1000 < Date.now() + 60_000; // 1-minute buffer
  } catch {
    return true;
  }
}

async function apiFetch(
  url: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), AUTH_FETCH_TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---------- internal helpers ----------

  const scheduleRefresh = useCallback((expiresIn = 900) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    const delay = Math.max((expiresIn - 60) * 1000, 30_000);
    refreshTimerRef.current = setTimeout(() => {
      refreshTokens();
    }, delay);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const setAuthenticated = useCallback((user: User, access: string, expiresIn = 900) => {
    setState({
      user,
      accessToken: access,
      isAuthenticated: true,
      isLoading: false,
    });
    scheduleRefresh(expiresIn);
  }, [scheduleRefresh]);

  const setUnauthenticated = useCallback(() => {
    clearTokens();
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    setState({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
  }, []);

  // ---------- token refresh ----------

  async function refreshTokens(): Promise<boolean> {
      const rawRefresh = getStoredRefresh();
      if (!rawRefresh) {
        setUnauthenticated();
        return false;
      }

      try {
        const resp = await apiFetch(`${AUTH_BASE}/refresh/`, {
          method: 'POST',
          body: JSON.stringify({ refresh_token: rawRefresh }),
        });

        if (!resp.ok) {
          setUnauthenticated();
          return false;
        }

        const data = await resp.json();
        storeTokens(data.access_token, data.refresh_token);
        if (data.user) {
          setAuthenticated(data.user, data.access_token, data.expires_in);
        }
        return true;
      } catch {
        setUnauthenticated();
        return false;
      }
    };

  // ---------- fetch profile ----------

  const fetchProfile = useCallback(async (token: string): Promise<User | null> => {
    try {
      const resp = await apiFetch(`${AUTH_BASE}/me/`, {}, token);
      if (!resp.ok) return null;
      return await resp.json();
    } catch {
      return null;
    }
  }, []);

  // ---------- init from stored token ----------

  useEffect(() => {
    const init = async () => {
      try {
        const access = getStoredToken();
        if (!access) {
          setState(prev => ({ ...prev, isLoading: false }));
          return;
        }

        if (isTokenExpired(access)) {
          const ok = await refreshTokens();
          if (!ok) setState(prev => ({ ...prev, isLoading: false }));
          return;
        }

        const user = await fetchProfile(access);
        if (user) {
          setAuthenticated(user, access);
        } else {
          const ok = await refreshTokens();
          if (!ok) setState(prev => ({ ...prev, isLoading: false }));
        }
      } catch {
        // Network hang/abort must never leave the app on an infinite spinner
        setUnauthenticated();
      }
    };

    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------- public methods ----------

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const resp = await apiFetch(`${AUTH_BASE}/v2/login/`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || 'Login failed');
      }

      const data = await resp.json();
      storeTokens(data.access_token, data.refresh_token);
      setAuthenticated(data.user, data.access_token, data.expires_in);
      return true;
    } catch (err) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw err;
    }
  }, [setAuthenticated]);

  const register = useCallback(async (userData: RegisterData): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const resp = await apiFetch(`${AUTH_BASE}/v2/register/`, {
        method: 'POST',
        body: JSON.stringify(userData),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || 'Registration failed');
      }

      const data = await resp.json();
      storeTokens(data.access_token, data.refresh_token);
      setAuthenticated(data.user, data.access_token, data.expires_in);
      try {
        const { trackEvent } = await import('@/lib/analytics');
        trackEvent('signup_completed', { email: userData.email });
      } catch {
        /* analytics optional */
      }
      return true;
    } catch (err) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw err;
    }
  }, [setAuthenticated]);

  const logout = useCallback(async (): Promise<void> => {
    const rawRefresh = getStoredRefresh();
    if (state.accessToken) {
      await apiFetch(
        `${AUTH_BASE}/logout-current/`,
        { method: 'POST', body: JSON.stringify({ refresh_token: rawRefresh || '' }) },
        state.accessToken,
      ).catch(() => {});
    }
    setUnauthenticated();
  }, [state.accessToken, setUnauthenticated]);

  const logoutAll = useCallback(async (): Promise<void> => {
    if (state.accessToken) {
      await apiFetch(
        `${AUTH_BASE}/logout-all/`,
        { method: 'POST' },
        state.accessToken,
      ).catch(() => {});
    }
    setUnauthenticated();
  }, [state.accessToken, setUnauthenticated]);

  // OAuth helpers: redirect to backend-provided URL
  const loginWithGoogle = useCallback(async (): Promise<boolean> => {
    const resp = await apiFetch(`${AUTH_BASE}/google/`, { method: 'POST' });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to initiate Google login');
    }
    const { authorization_url } = await resp.json();
    if (!authorization_url) throw new Error('No authorization URL returned');
    window.location.href = authorization_url;
    return true;
  }, []);

  const loginWithGitHub = useCallback(async (): Promise<boolean> => {
    const resp = await apiFetch(`${AUTH_BASE}/github/`, { method: 'POST' });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to initiate GitHub login');
    }
    const { authorization_url } = await resp.json();
    if (!authorization_url) throw new Error('No authorization URL returned');
    window.location.href = authorization_url;
    return true;
  }, []);

  const loginWithFirebase = useCallback(async (idToken: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const resp = await apiFetch(`${AUTH_BASE}/firebase/`, {
        method: 'POST',
        body: JSON.stringify({ id_token: idToken }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || 'Firebase login failed');
      }
      const data = await resp.json();
      storeTokens(data.access_token, data.refresh_token);
      setAuthenticated(data.user, data.access_token, data.expires_in);
      return true;
    } catch (err) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw err;
    }
  }, [setAuthenticated]);

  // Called after OAuth callback completes and URL has tokens
  const handleOAuthCallback = useCallback(async (access: string, refresh: string): Promise<void> => {
    storeTokens(access, refresh);
    const user = await fetchProfile(access);
    if (user) {
      setAuthenticated(user, access);
    }
  }, [fetchProfile, setAuthenticated]);

  const updateProfile = useCallback(async (data: Partial<User>): Promise<boolean> => {
    if (!state.accessToken) return false;
    const resp = await apiFetch(
      `${AUTH_BASE}/profile/update/`,
      { method: 'PATCH', body: JSON.stringify(data) },
      state.accessToken,
    );
    if (resp.ok) {
      const updated = await resp.json();
      setState(prev => ({ ...prev, user: updated }));
    }
    return resp.ok;
  }, [state.accessToken]);

  const changePassword = useCallback(async (
    currentPassword: string, newPassword: string
  ): Promise<boolean> => {
    if (!state.accessToken) return false;
    const resp = await apiFetch(
      `${AUTH_BASE}/change-password/`,
      {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      },
      state.accessToken,
    );
    return resp.ok;
  }, [state.accessToken]);

  const resetPassword = useCallback(async (email: string): Promise<boolean> => {
    const resp = await apiFetch(
      `${AUTH_BASE}/forgot-password/`,
      { method: 'POST', body: JSON.stringify({ email }) },
    );
    return resp.ok;
  }, []);

  const linkGoogle = useCallback(async (): Promise<string | null> => {
    if (!state.accessToken) return null;
    const resp = await apiFetch(
      `${AUTH_BASE}/link/google/`,
      { method: 'POST' },
      state.accessToken,
    );
    if (!resp.ok) return null;
    const { authorization_url } = await resp.json();
    return authorization_url;
  }, [state.accessToken]);

  const linkGitHub = useCallback(async (): Promise<string | null> => {
    if (!state.accessToken) return null;
    const resp = await apiFetch(
      `${AUTH_BASE}/link/github/`,
      { method: 'POST' },
      state.accessToken,
    );
    if (!resp.ok) return null;
    const { authorization_url } = await resp.json();
    return authorization_url;
  }, [state.accessToken]);

  const unlinkGoogle = useCallback(async (): Promise<boolean> => {
    if (!state.accessToken) return false;
    const resp = await apiFetch(
      `${AUTH_BASE}/unlink/google/`,
      { method: 'DELETE' },
      state.accessToken,
    );
    return resp.ok;
  }, [state.accessToken]);

  const unlinkGitHub = useCallback(async (): Promise<boolean> => {
    if (!state.accessToken) return false;
    const resp = await apiFetch(
      `${AUTH_BASE}/unlink/github/`,
      { method: 'DELETE' },
      state.accessToken,
    );
    return resp.ok;
  }, [state.accessToken]);

  const getSessions = useCallback(async (): Promise<Session[]> => {
    if (!state.accessToken) return [];
    const resp = await apiFetch(
      `${AUTH_BASE}/sessions/list/`,
      {},
      state.accessToken,
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return data.sessions || [];
  }, [state.accessToken]);

  const revokeSession = useCallback(async (sessionId: string): Promise<boolean> => {
    if (!state.accessToken) return false;
    const resp = await apiFetch(
      `${AUTH_BASE}/sessions/${sessionId}/revoke/`,
      { method: 'DELETE' },
      state.accessToken,
    );
    return resp.ok;
  }, [state.accessToken]);

  const hasPermission = useCallback((permission: string): boolean => {
    if (!state.user) return false;
    if (state.user.role === 'admin') return true;
    const rolePerms: Record<string, string[]> = {
      user: ['view_own', 'create_own', 'edit_own', 'delete_own'],
      viewer: ['view_own', 'view_shared'],
    };
    return (rolePerms[state.user.role] || []).includes(permission);
  }, [state.user]);

  const hasRole = useCallback((role: string): boolean => {
    return state.user?.role === role;
  }, [state.user]);

  const value: AuthContextType = {
    ...state,
    login,
    loginWithGoogle,
    loginWithGitHub,
    loginWithFirebase,
    register,
    logout,
    logoutAll,
    refreshTokens,
    updateProfile,
    changePassword,
    resetPassword,
    linkGoogle,
    linkGitHub,
    unlinkGoogle,
    unlinkGitHub,
    getSessions,
    revokeSession,
    hasPermission,
    hasRole,
    handleOAuthCallback,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};

export default AuthProvider;
