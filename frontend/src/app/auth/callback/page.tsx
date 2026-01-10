/**
 * OAuth callback page - handles redirects from OAuth providers (Google)
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { handleOAuthCallback } from "@/lib/contexts/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

type CallbackState = "loading" | "success" | "error";

export default function OAuthCallbackPage() {
  const [state, setState] = useState<CallbackState>("loading");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get("code");
      const oauthState = searchParams.get("state");
      const errorParam = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      // Handle OAuth error response
      if (errorParam) {
        setError(errorDescription || errorParam || "OAuth authentication failed");
        setState("error");
        return;
      }

      // Validate required parameters
      if (!code || !oauthState) {
        setError("Missing authentication parameters. Please try again.");
        setState("error");
        return;
      }

      try {
        // Process the OAuth callback
        await handleOAuthCallback(code, oauthState);
        setState("success");

        // Redirect to home page after brief delay
        setTimeout(() => {
          router.push("/");
        }, 1500);
      } catch (err: any) {
        console.error("OAuth callback error:", err);
        setError(err.message || "Failed to complete authentication");
        setState("error");
      }
    };

    processCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          {state === "loading" && (
            <>
              <div className="mx-auto mb-4">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
              <CardTitle>Completing Sign In</CardTitle>
              <CardDescription>
                Please wait while we verify your authentication...
              </CardDescription>
            </>
          )}

          {state === "success" && (
            <>
              <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle>Welcome!</CardTitle>
              <CardDescription>
                You have been successfully signed in. Redirecting...
              </CardDescription>
            </>
          )}

          {state === "error" && (
            <>
              <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <CardTitle>Authentication Failed</CardTitle>
              <CardDescription>
                {error || "An error occurred during sign in"}
              </CardDescription>
            </>
          )}
        </CardHeader>

        <CardContent>
          {state === "loading" && (
            <p className="text-sm text-muted-foreground text-center">
              This should only take a moment...
            </p>
          )}

          {state === "success" && (
            <div className="flex justify-center">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}

          {state === "error" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                Please try signing in again. If the problem persists, contact support.
              </p>
              <Button variant="outline" className="w-full" asChild>
                <Link href="/login">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Login
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
