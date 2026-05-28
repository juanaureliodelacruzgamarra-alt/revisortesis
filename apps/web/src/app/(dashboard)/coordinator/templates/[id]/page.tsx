import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { StructureTree } from "@/features/templates/structure-tree";
import { ApiError } from "@/lib/api/client";
import { fetchTemplate } from "@/lib/api/templates";
import { PROGRAM_LEVEL_LABELS, TEMPLATE_STATUS_LABELS } from "@/lib/api/types";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata = { title: "Plantilla · Aurelio" };

export default async function TemplateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role !== "coordinator" && user.role !== "admin") {
    redirect(`/${user.role}`);
  }

  const { id } = await params;
  let template;
  try {
    template = await fetchTemplate(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/coordinator/templates"
          className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-[color:var(--aurora-cream)]"
        >
          ← Volver a documentos patrón
        </Link>
      </div>

      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant={
              template.parsing_status === "parsed"
                ? "success"
                : template.parsing_status === "failed"
                  ? "destructive"
                  : "warning"
            }
          >
            {TEMPLATE_STATUS_LABELS[template.parsing_status]}
          </Badge>
          {template.is_active ? (
            <Badge>Activa</Badge>
          ) : (
            <Badge variant="outline">Inactiva</Badge>
          )}
          <Badge variant="muted">v{template.version}</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          {template.title}
        </h1>
        <p className="text-zinc-600 dark:text-[color:var(--aurora-cream-dim)]">
          {template.description ?? "Sin descripción."}
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Programa asociado</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            <span className="font-mono text-xs text-zinc-500">
              [{template.program.code}]
            </span>{" "}
            {template.program.name} ·{" "}
            <span className="text-zinc-500">
              {PROGRAM_LEVEL_LABELS[template.program.level]}
            </span>
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Archivo original</CardTitle>
          <CardDescription>
            Descarga el documento tal como fue subido.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
            <dt className="text-zinc-500">Nombre</dt>
            <dd className="font-mono break-all">
              {template.original_filename}
            </dd>
            <dt className="text-zinc-500">MIME</dt>
            <dd className="font-mono">{template.mime_type}</dd>
            <dt className="text-zinc-500">Tamaño</dt>
            <dd>
              {(template.file_size_bytes / 1024).toFixed(1)} KB
            </dd>
            <dt className="text-zinc-500">Subido</dt>
            <dd>{new Date(template.created_at).toLocaleString("es-PE")}</dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Estructura detectada</CardTitle>
          <CardDescription>
            Heurística basada en estilos de encabezado y numeración. La Fase 4
            refinará esta extracción con LLM.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {template.parsing_status === "failed" ? (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
              {template.parsing_error ?? "Error desconocido al procesar."}
            </p>
          ) : template.structure_json ? (
            <div className="space-y-3">
              <p className="text-xs text-zinc-500">
                {template.structure_json.sections.length} secciones de primer
                nivel · {template.structure_json.total_paragraphs} párrafos ·{" "}
                {template.structure_json.total_chars} caracteres
                {template.structure_json.page_count > 0
                  ? ` · ${template.structure_json.page_count} páginas`
                  : ""}
              </p>
              <StructureTree sections={template.structure_json.sections} />
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Aún procesando…</p>
          )}
        </CardContent>
      </Card>

      <div>
        <Button asChild variant="outline">
          <Link href="/coordinator/templates">Volver</Link>
        </Button>
      </div>
    </div>
  );
}
