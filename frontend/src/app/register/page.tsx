/**
 * Registration page with email/password signup
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, UserPlus, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";
import apiClient from "@/lib/api/client";

interface PasswordRequirements {
  min_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_digit: boolean;
  require_special: boolean;
  description: string;
}

interface PasswordValidation {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasDigit: boolean;
  hasSpecial: boolean;
}

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [requirements, setRequirements] = useState<PasswordRequirements | null>(null);
  const [validation, setValidation] = useState<PasswordValidation>({
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasDigit: false,
    hasSpecial: false,
  });
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  const { register } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  // Fetch password requirements on mount
  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const response = await apiClient.get("/auth/password-requirements");
        setRequirements(response.data);
      } catch (error) {
        // Use default requirements if API fails
        setRequirements({
          min_length: 8,
          require_uppercase: true,
          require_lowercase: true,
          require_digit: true,
          require_special: true,
          description: "Password must be at least 8 characters with uppercase, lowercase, number, and special character.",
        });
      }
    };
    fetchRequirements();
  }, []);

  // Validate password in real-time
  useEffect(() => {
    if (!requirements) return;

    setValidation({
      minLength: password.length >= requirements.min_length,
      hasUppercase: !requirements.require_uppercase || /[A-Z]/.test(password),
      hasLowercase: !requirements.require_lowercase || /[a-z]/.test(password),
      hasDigit: !requirements.require_digit || /\d/.test(password),
      hasSpecial: !requirements.require_special || /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
    });
  }, [password, requirements]);

  const isPasswordValid = Object.values(validation).every(Boolean);
  const doPasswordsMatch = password === confirmPassword && password.length > 0;

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isPasswordValid) {
      toast({
        title: "Invalid password",
        description: "Please ensure your password meets all requirements",
        variant: "destructive",
      });
      return;
    }

    if (!doPasswordsMatch) {
      toast({
        title: "Passwords don't match",
        description: "Please ensure both passwords are identical",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const result = await register(email, password, name || undefined);

      if (result.requiresVerification) {
        setRegistrationSuccess(true);
      } else {
        toast({
          title: "Registration successful",
          description: "You can now log in to your account",
        });
        router.push("/login");
      }
    } catch (error: any) {
      toast({
        title: "Registration failed",
        description: error.message || "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Show success message if registration completed
  if (registrationSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
            <CardTitle>Check your email</CardTitle>
            <CardDescription>
              We&apos;ve sent a verification link to <strong>{email}</strong>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground text-center">
              Click the link in the email to verify your account. The link will expire in 24 hours.
            </p>
            <div className="flex flex-col gap-2">
              <Button variant="outline" asChild>
                <Link href="/login">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Login
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Create Account</h1>
          <p className="text-muted-foreground">
            Sign up to save your API documents and chat history
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign Up</CardTitle>
            <CardDescription>
              Create a new account to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name (optional)</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />

                {/* Password Requirements Checklist */}
                {password.length > 0 && requirements && (
                  <div className="mt-2 space-y-1 text-xs">
                    <RequirementItem
                      met={validation.minLength}
                      text={`At least ${requirements.min_length} characters`}
                    />
                    {requirements.require_uppercase && (
                      <RequirementItem met={validation.hasUppercase} text="One uppercase letter (A-Z)" />
                    )}
                    {requirements.require_lowercase && (
                      <RequirementItem met={validation.hasLowercase} text="One lowercase letter (a-z)" />
                    )}
                    {requirements.require_digit && (
                      <RequirementItem met={validation.hasDigit} text="One number (0-9)" />
                    )}
                    {requirements.require_special && (
                      <RequirementItem met={validation.hasSpecial} text="One special character (!@#$%^&*)" />
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
                {confirmPassword.length > 0 && (
                  <div className="mt-1">
                    <RequirementItem
                      met={doPasswordsMatch}
                      text={doPasswordsMatch ? "Passwords match" : "Passwords do not match"}
                    />
                  </div>
                )}
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !isPasswordValid || !doPasswordsMatch}
              >
                {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                <UserPlus className="h-4 w-4 mr-2" />
                Create Account
              </Button>
            </form>

            <div className="mt-4 text-center text-sm">
              <span className="text-muted-foreground">Already have an account? </span>
              <Link href="/login" className="text-primary hover:underline font-medium">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>

        <p className="text-xs text-center text-muted-foreground">
          By creating an account, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}

// Helper component for password requirements
function RequirementItem({ met, text }: { met: boolean; text: string }) {
  return (
    <div className={`flex items-center gap-1.5 ${met ? "text-green-600" : "text-muted-foreground"}`}>
      {met ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      <span>{text}</span>
    </div>
  );
}
