/**
 * Authentication context for managing user authentication state
 * Supports email/password login, OAuth (Google), and guest mode
 */

"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import apiClient from "@/lib/api/client";

export interface User {
  id: string;
  email: string | null;
  name?: string;
  avatar_url?: string;
  is_verified?: boolean;
  is_admin?: boolean;
  is_guest?: boolean;
}

interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<{ requiresVerification: boolean }>;
  logout: () => void;
  continueAsGuest: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token storage keys
const TOKEN_STORAGE_KEY = "auth_tokens";
const USER_STORAGE_KEY = "auth_user";
const GUEST_STORAGE_KEY = "auth_guest";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isGuest: false,
    isLoading: true,
  });
  const [tokens, setTokens] = useState<TokenData | null>(null);

  // Get access token for API requests
  const getAccessToken = useCallback((): string | null => {
    return tokens?.access_token || null;
  }, [tokens]);

  // Store tokens and user
  const storeAuthData = useCallback((tokenData: TokenData, userData: User) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenData));
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
    localStorage.removeItem(GUEST_STORAGE_KEY);
    setTokens(tokenData);
    setAuthState({
      user: userData,
      isAuthenticated: true,
      isGuest: userData.is_guest || false,
      isLoading: false,
    });
  }, []);

  // Clear auth data
  const clearAuthData = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(GUEST_STORAGE_KEY);
    setTokens(null);
    setAuthState({
      user: null,
      isAuthenticated: false,
      isGuest: false,
      isLoading: false,
    });
  }, []);

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
      const storedUser = localStorage.getItem(USER_STORAGE_KEY);
      const isGuest = localStorage.getItem(GUEST_STORAGE_KEY) === "true";

      if (storedTokens && storedUser) {
        try {
          const tokenData = JSON.parse(storedTokens) as TokenData;
          const userData = JSON.parse(storedUser) as User;

          // Set tokens and user from storage
          setTokens(tokenData);
          setAuthState({
            user: userData,
            isAuthenticated: true,
            isGuest: userData.is_guest || false,
            isLoading: false,
          });
        } catch (error) {
          console.error("Failed to restore auth state", error);
          clearAuthData();
        }
      } else if (isGuest) {
        setAuthState({
          user: null,
          isAuthenticated: false,
          isGuest: true,
          isLoading: false,
        });
      } else {
        setAuthState(prev => ({ ...prev, isLoading: false }));
      }
    };

    initAuth();
  }, [clearAuthData]);

  // Login with email and password
  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post("/auth/login", { email, password });
      const { access_token, refresh_token, expires_in, user } = response.data;

      storeAuthData(
        { access_token, refresh_token, expires_in },
        {
          id: user.id,
          email: user.email,
          name: user.name,
          avatar_url: user.avatar_url,
          is_verified: user.is_verified,
          is_admin: user.is_admin,
          is_guest: false,
        }
      );
    } catch (error: any) {
      // API client transforms errors to have message directly
      const message = error.message || error.response?.data?.detail || "Invalid email or password";
      throw new Error(message);
    }
  };

  // Register new user
  const register = async (email: string, password: string, name?: string) => {
    try {
      const response = await apiClient.post("/auth/register", { email, password, name });
      return { requiresVerification: response.data.requires_verification };
    } catch (error: any) {
      // API client transforms errors - check both formats
      const detail = error.details?.detail || error.response?.data?.detail;
      if (typeof detail === "object" && detail.errors) {
        throw new Error(detail.errors.join(". "));
      }
      // Use error.message from API client transformation
      throw new Error(error.message || detail || "Registration failed. Please try again.");
    }
  };

  // Logout
  const logout = useCallback(() => {
    // Call logout endpoint (fire and forget)
    apiClient.post("/auth/logout").catch(() => {});
    clearAuthData();
  }, [clearAuthData]);

  // Continue as guest
  const continueAsGuest = async () => {
    try {
      const response = await apiClient.post("/auth/guest");
      const { access_token, refresh_token, expires_in, user } = response.data;

      storeAuthData(
        { access_token, refresh_token, expires_in },
        {
          id: user.id,
          email: null,
          name: user.name,
          is_guest: true,
          is_verified: false,
          is_admin: false,
        }
      );
      localStorage.setItem(GUEST_STORAGE_KEY, "true");
    } catch (error: any) {
      // Fallback to local guest mode if API fails
      localStorage.setItem(GUEST_STORAGE_KEY, "true");
      setAuthState({
        user: null,
        isAuthenticated: false,
        isGuest: true,
        isLoading: false,
      });
    }
  };

  // Login with Google OAuth
  const loginWithGoogle = async () => {
    try {
      // Get current URL as redirect URI
      const redirectUri = `${window.location.origin}/auth/callback`;

      // Get authorization URL from backend
      const response = await apiClient.get("/auth/oauth/google", {
        params: { redirect_uri: redirectUri },
      });

      const { authorization_url, state } = response.data;

      // Store state for verification
      sessionStorage.setItem("oauth_state", state);
      sessionStorage.setItem("oauth_redirect_uri", redirectUri);

      // Redirect to Google
      window.location.href = authorization_url;
    } catch (error: any) {
      const message = error.response?.data?.detail || "Failed to initiate Google login";
      throw new Error(message);
    }
  };

  // Handle OAuth callback
  const handleOAuthCallback = useCallback(async (code: string, state: string) => {
    const savedState = sessionStorage.getItem("oauth_state");
    const redirectUri = sessionStorage.getItem("oauth_redirect_uri");

    // Clear session storage
    sessionStorage.removeItem("oauth_state");
    sessionStorage.removeItem("oauth_redirect_uri");

    // Verify state
    if (state !== savedState) {
      throw new Error("Invalid OAuth state. Please try again.");
    }

    // Exchange code for tokens
    const response = await apiClient.get("/auth/oauth/google/callback", {
      params: { code, state, redirect_uri: redirectUri },
    });

    const { access_token, refresh_token, expires_in, user } = response.data;

    storeAuthData(
      { access_token, refresh_token, expires_in },
      {
        id: user.id,
        email: user.email,
        name: user.name,
        avatar_url: user.avatar_url,
        is_verified: user.is_verified,
        is_admin: user.is_admin,
        is_guest: false,
      }
    );
  }, [storeAuthData]);

  // Refresh tokens
  const refreshTokens = async () => {
    if (!tokens?.refresh_token) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await apiClient.post("/auth/refresh", {
        refresh_token: tokens.refresh_token,
      });

      const { access_token, refresh_token, expires_in, user } = response.data;

      storeAuthData(
        { access_token, refresh_token, expires_in },
        {
          id: user.id,
          email: user.email,
          name: user.name,
          avatar_url: user.avatar_url,
          is_verified: user.is_verified,
          is_admin: user.is_admin,
          is_guest: user.is_guest || false,
        }
      );
    } catch (error) {
      // Token refresh failed, clear auth
      clearAuthData();
      throw error;
    }
  };

  // Expose callback handler for use in OAuth callback page
  useEffect(() => {
    // @ts-ignore - attach to window for callback page
    window.__handleOAuthCallback = handleOAuthCallback;
    return () => {
      // @ts-ignore
      delete window.__handleOAuthCallback;
    };
  }, [handleOAuthCallback]);

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        register,
        logout,
        continueAsGuest,
        loginWithGoogle,
        refreshTokens,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// Export for OAuth callback handling
export async function handleOAuthCallback(code: string, state: string): Promise<void> {
  // @ts-ignore
  if (window.__handleOAuthCallback) {
    // @ts-ignore
    await window.__handleOAuthCallback(code, state);
  } else {
    throw new Error("Auth context not initialized");
  }
}
