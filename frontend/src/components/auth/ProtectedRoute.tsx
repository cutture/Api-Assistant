/**
 * Protected route wrapper that redirects to login if not authenticated
 * Allows guest access for local testing
 */

"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isGuest, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Don't redirect if already on login page
    if (pathname === "/login") {
      return;
    }

    // If not loading and not authenticated and not guest, redirect to login
    if (!isLoading && !isAuthenticated && !isGuest) {
      router.push("/login");
    }
  }, [isAuthenticated, isGuest, isLoading, pathname, router]);

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

  // If on login page, show it
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // If authenticated or guest, show children
  if (isAuthenticated || isGuest) {
    return <>{children}</>;
  }

  // Otherwise, return null (will redirect to login)
  return null;
}
