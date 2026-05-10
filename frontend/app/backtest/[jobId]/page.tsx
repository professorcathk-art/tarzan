"use client";

import { useParams } from "next/navigation";

import { useEffect, useState } from "react";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type JobState = {
  status: string;
  metrics?: Record<string, unknown> | null;
  equity_curve?: { week: number; portfolio: number; benchmark: number }[] | null;
};

export default function BacktestPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params?.jobId;
  const [data, setData] = useState<JobState | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return undefined;
    let stop = false;
    async function poll() {
      try {
        const res = await apiFetch<JobState>(`/api/backtest/${jobId}`);
        if (!stop) setData(res);
      } catch (e) {
        if (!stop) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    }
    void poll();
    const handle = window.setInterval(poll, 3000);
    return () => {
      stop = true;
      window.clearInterval(handle);
    };
  }, [jobId]);

  const chartReady = Array.isArray(data?.equity_curve) && (data.equity_curve?.length ?? 0) > 0;

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div>
        <p className="text-sm text-muted-foreground">Backtest job {jobId ?? "…"}</p>
        <h1 className="text-2xl font-semibold">Performance report</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Polls the API every three seconds until the FastAPI worker finishes its weekly rebalance proxy.
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          Disclaimer: hypothetical backtests are not indicative of future results.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          {!data ? <p>Awaiting snapshot…</p> : <p>{data.status}</p>}
          {data?.metrics ? (
            <pre className="mt-2 overflow-auto rounded-lg bg-muted p-3 text-xs">
              {JSON.stringify(data.metrics, null, 2)}
            </pre>
          ) : null}
          {!data?.metrics && data?.status === "completed" ? (
            <p className="text-muted-foreground">No metrics persisted.</p>
          ) : null}
          {err ? <p className="text-destructive">{err}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Equity curve (portfolio vs benchmark)</CardTitle>
        </CardHeader>
        <CardContent className="h-96">
          {chartReady ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.equity_curve || []}>
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="portfolio" stroke="#6366f1" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="benchmark" stroke="#94a3b8" strokeWidth={1} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              Waiting for weekly equity samples…
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
