import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function TemplatesPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Templates</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your Supabase session and call `/api/templates` once JWTs embed `tier` metadata for billing gates.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <Link href="/screener" className={cn(buttonVariants({ variant: "outline" }))}>
            Run a pipeline
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
