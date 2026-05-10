import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function TemplateDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <h1 className="text-2xl font-semibold">Template editor</h1>
      <p className="text-sm text-muted-foreground">
        Editing template <code>{params.id}</code> — hydrate from <code>/api/templates/{params.id}</code>.
      </p>
      <Card>
        <CardHeader>
          <CardTitle>Shortcuts</CardTitle>
        </CardHeader>
        <CardContent>
          <Link href="/templates" className={cn(buttonVariants({ variant: "outline" }))}>
            Back to list
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
