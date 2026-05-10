"use client";

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { apiFetch } from "@/lib/api";

type StratMeta = {

  slug: string;

  name: string;

  category: string;

  is_premium?: boolean;



  sharpe_preview?: number;
};

type PipelineStage = {
  uid: string;
  slug: string;


  filter_mode: "hard" | "soft";

  keep_pct: number;



  params: Record<string, unknown>;
};

function SortableStage({ stage, index, onChange, onRemove }: {
  stage: PipelineStage;


  index: number;





  onChange: (idx: number, patch: Partial<PipelineStage>) => void;



  onRemove: (idx: number) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: stage.uid,

  });


  const style = {
    transform: CSS.Transform.toString(transform),

    transition,




    opacity: isDragging ? 0.85 : 1,




  };


  return (

    <div ref={setNodeRef} style={style} className="rounded-lg border bg-card p-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">

        <div className="flex items-center gap-2">

          <button
            type="button"
            className="cursor-grab touch-none rounded border px-2 py-1 text-xs"

            {...attributes}

            {...listeners}
          >
            ⋮⋮
          </button>







          <div>

            <p className="font-medium">

              Stage {index + 1}: {stage.slug}




            </p>

            <p className="text-xs text-muted-foreground">Reorder with drag handle</p>
          </div>

        </div>

        <Button variant="outline" size="sm" type="button" onClick={() => onRemove(index)}>



          Remove

        </Button>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">

        <div>


          <Label className="text-xs">Filter mode</Label>






          <Select

            value={stage.filter_mode}

            onValueChange={(v) => {
              if (v === "hard" || v === "soft") onChange(index, { filter_mode: v });
            }}
          >
            <SelectTrigger className="mt-1">

              <SelectValue />
            </SelectTrigger>






            <SelectContent>






              <SelectItem value="hard">Hard — must signal</SelectItem>



              <SelectItem value="soft">Soft — top % by score</SelectItem>



            </SelectContent>
          </Select>
        </div>
        <div>



          <Label className="text-xs">Keep top % (soft)</Label>



          <Input




            type="number"
            min={0.05}




            step={0.05}






            max={1}






            disabled={stage.filter_mode === "hard"}

            className="mt-1"


            value={stage.keep_pct}

            onChange={(e) =>
              onChange(index, {

                keep_pct: Number.parseFloat(e.target.value),

              })}
          />
        </div>
      </div>
    </div>
  );
}

export function ScreenerClient() {


  const router = useRouter();



  const [strategies, setStrategies] = useState<StratMeta[]>([]);



  const [stages, setStages] = useState<PipelineStage[]>([
    {
      uid: crypto.randomUUID(),
      slug: "trend_template",
      filter_mode: "hard",
      keep_pct: 0.3,
      params: {},
    },
    {
      uid: crypto.randomUUID(),
      slug: "vcp",
      filter_mode: "soft",
      keep_pct: 0.25,
      params: {},
    },
  ]);

  const [universe, setUniverse] = useState("sp500");

  const [mode, setMode] = useState<"waterfall" | "voting">("waterfall");


  const [maxResults, setMaxResults] = useState(25);





  const [running, setRunning] = useState(false);


  const sensors = useSensors(


    useSensor(PointerSensor),

    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,




    }),


  );

  useEffect(() => {


    apiFetch<StratMeta[]>("/api/strategies")






      .then(setStrategies)




      .catch((e: Error) => toast.error(`Load strategies failed: ${e.message}`));


  }, []);





  function onDragEnd(evt: DragEndEvent) {


    const { active, over } = evt;


    if (!over || active.id === over.id) return;


    setStages((items) => {




      const oldIndex = items.findIndex((s) => s.uid === active.id);


      const newIndex = items.findIndex((s) => s.uid === over.id);





      return arrayMove(items, oldIndex, newIndex);



    });


  }



  const funnelPreview = useMemo(() => {


    const est = "~3k tickers";


    const lines = [`Universe (${universe})  ${est}`];


    let factor = mode === "waterfall" ? 0.62 : 0.9;



    stages.forEach((s, idx) => {




      factor *= mode === "waterfall" ? (s.filter_mode === "hard" ? 0.18 : Number(s.keep_pct)) : 0.95;



      lines.push(`${idx + 1}. ${s.slug} → retain ~${(factor * 100).toFixed(0)}% of prior stage`);

    });

    lines.push(`Final slice → top ${maxResults} names`);


    return lines;


  }, [stages, universe, mode, maxResults]);




  async function runPipeline() {



    setRunning(true);


    try {




      const body = {

        pipeline_mode: mode,


        universe,


        max_results: maxResults,


        direction: "long",


        stages: stages.map((s, i) => ({

          slug: s.slug,


          order: i + 1,


          filter_mode: s.filter_mode,



          keep_pct: s.keep_pct,



          params: s.params,


        })),


        enqueue_backtest: false,


      };




      const res = await apiFetch<{ run_id: string; warnings?: string[]; data_stale_banner?: string | null }>(
        "/api/screen/run",
        { method: "POST", body: JSON.stringify(body) },
      );

      if (res.data_stale_banner) toast.warning(res.data_stale_banner);


      if (res.warnings?.length) res.warnings.forEach((w) => toast.message(w));

      toast.success("Screen complete");

      router.push(`/screener/results/${res.run_id}`);

    } catch (e) {

      const msg = e instanceof Error ? e.message : "Run failed";

      toast.error(msg);

    } finally {

      setRunning(false);

    }

  }

  return (

    <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1.1fr_0.9fr]">

      <div className="space-y-4">

        <div>


          <h1 className="text-2xl font-semibold tracking-tight">Waterfall screener</h1>

          <p className="text-sm text-muted-foreground mt-1">

            Stack alternative-data and technical strategies in order. Hard filters require a valid signal; soft filters

            keep the top fraction by score.

          </p>

        </div>

        <Card>

          <CardHeader>

            <CardTitle className="text-base">Strategy library</CardTitle>

          </CardHeader>

          <CardContent className="grid gap-2 sm:grid-cols-2">

            {strategies.map((s) => (

              <div key={s.slug} className="flex items-center justify-between rounded-md border p-2">

                <div>

                  <p className="text-sm font-medium">{s.name}</p>

                  <div className="flex gap-2 mt-1">

                    <Badge variant="secondary" className="text-[10px]">

                      {s.category}

                    </Badge>

                    {s.is_premium ? (

                      <Badge variant="outline" className="text-[10px]">

                        Pro

                      </Badge>

                    ) : null}

                  </div>

                </div>

                <Button
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={() =>

                    setStages((prev) => [
                      ...prev,

                      {
                        uid: crypto.randomUUID(),

                        slug: s.slug,

                        filter_mode: "hard",

                        keep_pct: 0.3,

                        params: {},

                      },

                    ])
                  }
                >
                  Add
                </Button>
              </div>
            ))}

          </CardContent>

        </Card>

        <Card>

          <CardHeader>

            <CardTitle className="text-base">Pipeline builder</CardTitle>

          </CardHeader>

          <CardContent className="space-y-3">

            <div className="grid gap-3 sm:grid-cols-2">

              <div>

                <Label>Universe</Label>

                <Select value={universe} onValueChange={(v) => v != null && v !== "" && setUniverse(v)}>

                  <SelectTrigger className="mt-1">

                    <SelectValue />

                  </SelectTrigger>

                  <SelectContent>

                    <SelectItem value="sp500">S&amp;P 500 sample</SelectItem>

                    <SelectItem value="all_us_equities">All US (proxy list — Pro)</SelectItem>

                  </SelectContent>

                </Select>

              </div>

              <div>

                <Label>Engine</Label>

                <Select value={mode} onValueChange={(v) => {
                  if (v === "waterfall" || v === "voting") setMode(v);
                }}>

                  <SelectTrigger className="mt-1">

                    <SelectValue />

                  </SelectTrigger>

                  <SelectContent>

                    <SelectItem value="waterfall">Waterfall</SelectItem>

                    <SelectItem value="voting">Voting (advanced)</SelectItem>

                  </SelectContent>

                </Select>

              </div>

            </div>

            <div>

              <Label>Max results</Label>

              <Input

                className="mt-1 max-w-xs"

                type="number"

                min={1}

                max={200}

                value={maxResults}

                onChange={(e) => setMaxResults(Number.parseInt(e.target.value || "10", 10))}

              />

            </div>

            <Separator />

            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>

              <SortableContext items={stages.map((s) => s.uid)} strategy={verticalListSortingStrategy}>

                <div className="space-y-2">

                  {stages.map((stage, idx) => (

                    <SortableStage

                      key={stage.uid}

                      stage={stage}

                      index={idx}

                      onChange={(i, patch) =>

                        setStages((prev) => prev.map((row, j) => (j === i ? { ...row, ...patch } : row)))

                      }

                      onRemove={(i) => setStages((prev) => prev.filter((_, j) => j !== i))}

                    />

                  ))}

                </div>

              </SortableContext>

            </DndContext>

            <Button className="w-full" type="button" disabled={running || stages.length === 0} onClick={runPipeline}>

              {running ? "Running…" : "Run pipeline"}

            </Button>

          </CardContent>

        </Card>

      </div>

      <div className="space-y-4">

        <Card>

          <CardHeader>

            <CardTitle className="text-base">Funnel preview</CardTitle>

          </CardHeader>

          <CardContent className="space-y-2 text-sm text-muted-foreground">

            {funnelPreview.map((line) => (

              <p key={line}>{line}</p>

            ))}

          </CardContent>

        </Card>

        <Card>

          <CardHeader>

            <CardTitle className="text-base">Runtime notes</CardTitle>

          </CardHeader>

          <CardContent className="text-sm text-muted-foreground space-y-2">

            <p>Each strategy times out after ~10s; skips surface as warnings.</p>

            <p className="flex items-center gap-2">

              <Switch checked disabled className="opacity-60" />

              FinBERT worker hook is server-side only (Pro).

            </p>

          </CardContent>

        </Card>

      </div>

    </div>
  );
}
