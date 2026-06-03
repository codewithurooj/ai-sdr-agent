import { redirect } from "next/navigation";

// The dashboard (/) is the campaigns list — redirect to keep URLs clean.
export default function CampaignsPage() {
  redirect("/dashboard");
}
