export const dynamic = "force-dynamic";


import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type RunRow = {
  ticker: string;
  rs?: number;
  sentiment?: number;
  score?: number;
  reason_summary?: string;
};

export default async function ResultsPage({ params }: { params: { runId: string } }) {
  const data = await apiFetch<{
    run_id: string;
    snapshots: unknown[];
    merged_table: RunRow[];
  }>(`/api/screen/${params.runId}`);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div>
        <p className="text-sm text-muted-foreground">Run {data.run_id}</p>
        <h1 className="text-2xl font-semibold tracking-tight">Waterfall results</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          過去績效與即時篩選結果不構成投資建議。資訊僅供研究參考。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Stage snapshots</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap break-words text-xs text-muted-foreground">
            {JSON.stringify(data.snapshots, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Final basket</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Ticker</TableHead>
                <TableHead>RS</TableHead>
                <TableHead>Sentiment</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Summary</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.merged_table.map((row, idx) => (
                <TableRow key={`${row.ticker}-${idx}`}>
                  <TableCell>{idx + 1}</TableCell>
                  <TableCell className="font-medium">{row.ticker}</TableCell>
                  <TableCell>{row.rs?.toFixed?.(1) ?? "—"}</TableCell>
                  <TableCell>{row.sentiment?.toFixed?.(2) ?? "—"}</TableCell>
                  <TableCell>{row.score?.toFixed?.(1) ?? "—"}</TableCell>
                  <TableCell className="max-w-xl text-sm text-muted-foreground">
                    {row.reason_summary}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
