import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-12 px-4 py-16">
      <section className="space-y-6 text-center">
        <Badge variant="secondary" className="mx-auto">
          Tarzan
        </Badge>
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
          Multi-strategy waterfall screening
        </h1>
        <p className="text-lg text-muted-foreground">
          Chain sentiment, technician, breakout, insider, fundamental, and volatility modules with transparent stage
          accounting, asynchronous backtests, saved templates, and scheduled email deltas.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/screener" className={cn(buttonVariants({ size: "lg" }))}>
            Open screener
          </Link>
          <Link href="/templates" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            Templates
          </Link>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Plans</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Free tier limits stages, universes, and premium alternative-data lanes.</p>
            <p>Pro unlocks deeper universes, email schedules via APScheduler + Resend, and Stripe-managed billing.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Risk disclosure</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Past screening and hypothetical backtests are not indicative of future results. Not investment advice.
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
