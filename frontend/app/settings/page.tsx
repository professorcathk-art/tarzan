import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card>
        <CardHeader>
          <CardTitle>Billing</CardTitle>
          <CardDescription>Stripe Checkout + Portal endpoints will live beside FastAPI Stripe webhooks.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Set <code>STRIPE_SECRET_KEY</code> and <code>STRIPE_WEBHOOK_SECRET</code> server-side plus publishable keys in the
          front-end bundle when you wire Checkout.
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Email schedules</CardTitle>
          <CardDescription>Pro-tier APScheduler hooks write into `email_schedules` and Resend via `sender.py`.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Configure <code>RESEND_API_KEY</code>, <code>RESEND_FROM_EMAIL</code>, and enable <code>ENABLE_SCHEDULER=1</code> on
          the API host once Postgres is reachable.
        </CardContent>
      </Card>

      <p className="text-sm">
        Need auth? Jump to{" "}
        <Link href="/auth/login" className="underline">
          login
        </Link>
        .
      </p>
    </div>
  );
}
