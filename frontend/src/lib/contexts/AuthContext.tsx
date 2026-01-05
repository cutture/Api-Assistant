/**
 * Authentication context for managing user authentication state
 * Supports both authenticated and guest mode for local testing
 */

"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  continueAsGuest: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isGuest: false,
    isLoading: true,
  });

  // Check for existing session on mount
  useEffect(() => {
    const storedUser = localStorage.getItem("auth_user");
    const isGuest = localStorage.getItem("auth_guest") === "true";

    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setAuthState({
          user,
          isAuthenticated: true,
          isGuest: false,
          isLoading: false,
        });
      } catch (error) {
        console.error("Failed to parse stored user", error);
        setAuthState((prev) => ({ ...prev, isLoading: false }));
      }
    } else if (isGuest) {
      setAuthState({
        user: null,
        isAuthenticated: false,
        isGuest: true,
        isLoading: false,
      });
    } else {
      setAuthState((prev) => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // TODO: Replace with actual API call
      // For now, simulating authentication
      const mockUser: User = {
        id: "user-123",
        email,
        name: email.split("@")[0],
        role: "user",
      };

      localStorage.setItem("auth_user", JSON.stringify(mockUser));
      localStorage.removeItem("auth_guest");

      setAuthState({
        user: mockUser,
        isAuthenticated: true,
        isGuest: false,
        isLoading: false,
      });
    } catch (error) {
      console.error("Login failed", error);
      throw new Error("Authentication failed. Please check your credentials.");
    }
  };

  const logout = () => {
    localStorage.removeItem("auth_user");
    localStorage.removeItem("auth_guest");

    setAuthState({
      user: null,
      isAuthenticated: false,
      isGuest: false,
      isLoading: false,
    });
  };

  const continueAsGuest = () => {
    localStorage.setItem("auth_guest", "true");

    setAuthState({
      user: null,
      isAuthenticated: false,
      isGuest: true,
      isLoading: false,
    });
  };

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        logout,
        continueAsGuest,
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
