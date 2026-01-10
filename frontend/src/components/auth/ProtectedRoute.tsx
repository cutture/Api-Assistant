/**
 * Protected route wrapper that redirects to login if not authenticated
 * Allows guest access for local testing
 */

"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import { Loader2 } from "lucide-react";

// Public routes that don't require authentication
const PUBLIC_ROUTES = ["/login", "/register", "/auth/callback"];

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isGuest, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Check if current path is a public route
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));

  useEffect(() => {
    // Don't redirect if on a public route
    if (isPublicRoute) {
      return;
    }

    // If not loading and not authenticated and not guest, redirect to login
    if (!isLoading && !isAuthenticated && !isGuest) {
      router.push("/login");
    }
  }, [isAuthenticated, isGuest, isLoading, pathname, router, isPublicRoute]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // If on a public route, show it
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // If authenticated or guest, show children
  if (isAuthenticated || isGuest) {
    return <>{children}</>;
  }

  // Otherwise, return null (will redirect to login)
  return null;
}
