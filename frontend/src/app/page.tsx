/**
 * Home page - Redirects to Chat (main feature)
 */

import { redirect } from "next/navigation";

export default function Home() {
  redirect("/chat");
}
