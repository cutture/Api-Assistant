/**
 * Main navigation bar component
 */

"use client";

import Link from "next/link";
import { FileText, Search, MessageSquare, Settings, Users, Network, LogOut, UserCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { ThemeToggle } from "@/components/theme-toggle";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isGuest, logout } = useAuth();
  const { toast } = useToast();

  const handleLogout = () => {
    logout();
    toast({
      title: "Signed out",
      description: "You have been signed out successfully",
    });
    router.push("/login");
  };

  const navItems = [
    {
      href: "/",
      label: "Documents",
      icon: FileText,
    },
    {
      href: "/search",
      label: "Search",
      icon: Search,
    },
    {
      href: "/chat",
      label: "Chat",
      icon: MessageSquare,
    },
    {
      href: "/sessions",
      label: "Sessions",
      icon: Users,
    },
    {
      href: "/diagrams",
      label: "Diagrams",
      icon: Network,
    },
  ];

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <FileText className="h-5 w-5" />
              </div>
              <span className="text-xl font-bold">API Assistant</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    size="sm"
                    className={cn(
                      "flex items-center space-x-2",
                      isActive && "bg-secondary"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Button>
                </Link>
              );
            })}
          </div>

          {/* Theme Toggle, Settings and User Menu */}
          <div className="flex items-center space-x-2">
            <ThemeToggle />

            <Link href="/settings">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>

            {/* User Info and Logout */}
            <div className="flex items-center space-x-2 border-l pl-2">
              {user && (
                <div className="flex items-center space-x-2 px-2">
                  <UserCircle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">{user.name || user.email}</span>
                </div>
              )}
              {isGuest && (
                <div className="flex items-center space-x-2 px-2">
                  <UserCircle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Guest</span>
                </div>
              )}
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
