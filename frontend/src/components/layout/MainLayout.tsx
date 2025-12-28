/**
 * Main application layout with navbar, sidebar, and footer
 */

"use client";

import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { Footer } from "./Footer";

interface MainLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
}

export function MainLayout({ children, showSidebar = true }: MainLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <div className="flex flex-1">
        {showSidebar && <Sidebar />}

        <main className="flex-1 overflow-auto">
          <div className="container mx-auto p-6">
            {children}
          </div>
        </main>
      </div>

      <Footer />
    </div>
  );
}
