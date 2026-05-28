import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  CITATION_STATUS_LABELS,
  type Citation,
  type CitationStatus,
} from "@/lib/api/types";

const STATUS_ORDER: CitationStatus[] = [
  "hallucinated",
  "not_found",
  "partial",
  "verified",
  "pending",
];

function statusVariant(s: CitationStatus) {
  switch (s) {
    case "verified":
      return "success" as const;
    case "partial":
      return "warning" as const;
    case "not_found":
      return "destructive" as const;
    case "hallucinated":
      return "destructive" as const;
    case "pending":
      return "muted" as const;
  }
}

function searchHref(citation: Citation): string {
  const q = citation.title ?? citation.raw_text.slice(0, 200);
  return `https://scholar.google.com/scholar?q=${encodeURIComponent(q)}`;
}

export function CitationsPanel({
  citations,
  emptyMessage,
}: {
  citations: Citation[];
  emptyMessage: string;
}) {
  if (citations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Validación de citas (CrossRef)</CardTitle>
          <CardDescription>{emptyMessage}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const counts: Record<CitationStatus, number> = {
    pending: 0,
    verified: 0,
    partial: 0,
    not_found: 0,
    hallucinated: 0,
  };
  for (const c of citations) counts[c.crossref_status]++;

  const sorted = [...citations].sort(
    (a, b) =>
      STATUS_ORDER.indexOf(a.crossref_status) -
      STATUS_ORDER.indexOf(b.crossref_status),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Validación de citas (CrossRef)</CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2">
          <span>{citations.length} referencias detectadas:</span>
          {STATUS_ORDER.filter((s) => counts[s] > 0).map((s) => (
            <Badge key={s} variant={statusVariant(s)}>
              {counts[s]} {CITATION_STATUS_LABELS[s].toLowerCase()}
            </Badge>
          ))}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {sorted.map((c) => (
            <li
              key={c.id}
              className="rounded-md border border-zinc-200 p-3 text-sm dark:border-[color:rgba(196,181,253,0.12)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusVariant(c.crossref_status)}>
                  {CITATION_STATUS_LABELS[c.crossref_status]}
                </Badge>
                {c.year ? (
                  <span className="text-xs text-zinc-500">({c.year})</span>
                ) : null}
                {c.doi ? (
                  <a
                    href={`https://doi.org/${c.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-xs text-zinc-500 hover:underline"
                  >
                    {c.doi}
                  </a>
                ) : null}
              </div>

              {c.title ? (
                <p className="mt-2 font-medium text-zinc-900 dark:text-[color:var(--aurora-cream)]">
                  {c.title}
                </p>
              ) : null}

              {c.authors ? (
                <p className="text-xs text-zinc-500">{c.authors}</p>
              ) : null}

              {c.journal ? (
                <p className="text-xs italic text-zinc-500">{c.journal}</p>
              ) : null}

              {c.crossref_message ? (
                <p className="mt-2 rounded bg-zinc-50 px-2 py-1.5 text-xs text-zinc-700 dark:bg-[rgba(20,22,62,0.55)]/60 dark:text-[color:var(--aurora-cream-dim)]">
                  {c.crossref_message}
                </p>
              ) : null}

              <details className="mt-2">
                <summary className="cursor-pointer text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-[color:var(--aurora-cream)]">
                  Ver texto original
                </summary>
                <p className="mt-1 whitespace-pre-wrap text-xs text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
                  {c.raw_text}
                </p>
              </details>

              {c.crossref_status !== "verified" ? (
                <a
                  href={searchHref(c)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-xs font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-[color:var(--aurora-cream)]"
                >
                  Buscar en Google Scholar →
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
