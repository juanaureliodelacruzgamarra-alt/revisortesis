import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/cn";

export function KpiCard({
  label,
  value,
  helper,
  tone = "default",
}: {
  label: string;
  value: string | number;
  helper?: string;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  const toneClass =
    tone === "success"
      ? "text-emerald-600 dark:text-emerald-300"
      : tone === "warning"
        ? "text-amber-600 dark:text-amber-300"
        : tone === "danger"
          ? "text-rose-600 dark:text-rose-300"
          : "text-zinc-900 dark:text-[color:var(--aurora-cream)]";
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium uppercase tracking-widest text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p
          className={cn(
            "aurora-display text-3xl font-semibold tabular-nums",
            toneClass,
          )}
        >
          {value}
        </p>
        {helper ? (
          <p className="mt-1 text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
            {helper}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
