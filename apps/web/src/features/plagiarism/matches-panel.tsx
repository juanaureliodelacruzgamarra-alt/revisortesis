import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PlagiarismMatch } from "@/lib/api/types";

function similarityVariant(sim: number) {
  if (sim >= 0.95) return "destructive" as const;
  if (sim >= 0.85) return "warning" as const;
  return "muted" as const;
}

function groupByMatchedVersion(
  matches: PlagiarismMatch[],
): { matched_version_id: string; matched_student_name: string; matched_submission_title: string; items: PlagiarismMatch[] }[] {
  const map = new Map<
    string,
    {
      matched_version_id: string;
      matched_student_name: string;
      matched_submission_title: string;
      items: PlagiarismMatch[];
    }
  >();
  for (const m of matches) {
    const key = m.matched_version_id;
    if (!map.has(key)) {
      map.set(key, {
        matched_version_id: m.matched_version_id,
        matched_student_name: m.matched_student_name,
        matched_submission_title: m.matched_submission_title,
        items: [],
      });
    }
    map.get(key)!.items.push(m);
  }
  return Array.from(map.values()).sort(
    (a, b) =>
      Math.max(...b.items.map((i) => i.similarity)) -
      Math.max(...a.items.map((i) => i.similarity)),
  );
}

export function PlagiarismPanel({
  matches,
  emptyMessage,
}: {
  matches: PlagiarismMatch[];
  emptyMessage: string;
}) {
  if (matches.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Detección de plagio</CardTitle>
          <CardDescription>{emptyMessage}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const groups = groupByMatchedVersion(matches);
  const totalGroups = groups.length;
  const highestSim = Math.max(...matches.map((m) => m.similarity));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detección de plagio</CardTitle>
        <CardDescription>
          {totalGroups} avance{totalGroups === 1 ? "" : "s"} con texto similar ·
          máximo {(highestSim * 100).toFixed(1)}%
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {groups.map((g) => (
          <div
            key={g.matched_version_id}
            className="rounded-lg border border-zinc-200 p-4 dark:border-[color:rgba(196,181,253,0.12)]"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-medium">
                {g.matched_student_name} —{" "}
                <span className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
                  {g.matched_submission_title}
                </span>
              </p>
              <Badge variant={similarityVariant(Math.max(...g.items.map((i) => i.similarity)))}>
                hasta {(Math.max(...g.items.map((i) => i.similarity)) * 100).toFixed(1)}%
              </Badge>
            </div>
            <p className="mt-1 text-xs text-zinc-500">
              {g.items.length} fragmento{g.items.length === 1 ? "" : "s"} con
              alta similitud
            </p>

            <ul className="mt-3 space-y-3">
              {g.items.map((m) => (
                <li
                  key={m.id}
                  className="rounded-md bg-zinc-50 p-3 text-sm dark:bg-[rgba(20,22,62,0.55)]/60"
                >
                  <div className="flex items-center justify-between">
                    <Badge variant={similarityVariant(m.similarity)}>
                      {(m.similarity * 100).toFixed(1)}%
                    </Badge>
                    {m.source_chunk.section ? (
                      <span className="text-xs text-zinc-500">
                        en {m.source_chunk.section}
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                        Fragmento del avance
                      </p>
                      <p className="mt-1 line-clamp-6 text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
                        {m.source_chunk.text}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                        Fragmento similar
                      </p>
                      <p className="mt-1 line-clamp-6 text-zinc-700 dark:text-[color:var(--aurora-cream-dim)]">
                        {m.matched_chunk.text}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
