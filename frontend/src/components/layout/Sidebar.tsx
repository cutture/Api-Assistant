/**
 * Sidebar component for quick info and navigation
 */

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Code, Zap, Shield } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-muted/20 p-4">
      <div className="space-y-4">
        {/* Features */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <span>Features</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <FeatureItem
              icon={Code}
              label="Code Generation"
              description="Multi-language support"
            />
            <FeatureItem
              icon={Shield}
              label="Security Scanning"
              description="Vulnerability detection"
            />
          </CardContent>
        </Card>

        {/* Quick Info */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Quick Info</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <p>Start a chat to generate code</p>
            <p>Supports Python, JS, TS, Java, Go, C#</p>
          </CardContent>
        </Card>
      </div>
    </aside>
  );
}

interface FeatureItemProps {
  icon: React.ElementType;
  label: string;
  description: string;
}

function FeatureItem({ icon: Icon, label, description }: FeatureItemProps) {
  return (
    <div className="flex items-start space-x-2">
      <Icon className="h-4 w-4 mt-0.5 text-muted-foreground" />
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
