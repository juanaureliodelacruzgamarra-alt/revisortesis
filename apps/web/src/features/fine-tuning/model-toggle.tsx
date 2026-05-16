"use client";

import { useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  updateModelPreferenceAction,
  type ModelPreference,
} from "@/lib/api/fine-tuning";

const GEMINI_MODELS = [
  "gemini-2.0-flash",
  "gemini-2.0-flash-lite",
  "gemini-1.5-pro",
  "gemini-1.5-flash",
];

export function ModelToggle({ pref }: { pref: ModelPreference }) {
  const [model, setModel] = useState(pref.model);
  const [fineTunedModel, setFineTunedModel] = useState(
    pref.fine_tuned_model ?? "",
  );
  const [useFineTuned, setUseFineTuned] = useState(pref.use_fine_tuned);
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  function save() {
    setError(null);
    setOk(false);
    start(async () => {
      const result = await updateModelPreferenceAction({
        model,
        fine_tuned_model: fineTunedModel || null,
        use_fine_tuned: useFineTuned,
      });
      if (!result.ok) setError(result.error);
      else setOk(true);
    });
  }

  const activeModel =
    pref.use_fine_tuned && pref.fine_tuned_model
      ? pref.fine_tuned_model
      : pref.model;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={pref.use_fine_tuned ? "success" : "muted"}>
          Activo: {activeModel}
        </Badge>
        <Badge variant="outline">proveedor: {pref.provider}</Badge>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor="gemini-model">Modelo Gemini</Label>
          <input
            id="gemini-model"
            list="gemini-model-list"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="aurora-input flex h-10 w-full rounded-md px-3 text-sm"
            placeholder="gemini-2.0-flash"
          />
          <datalist id="gemini-model-list">
            {GEMINI_MODELS.map((m) => (
              <option key={m} value={m} />
            ))}
          </datalist>
          <p className="text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
            Configura GEMINI_API_KEY en apps/api/.env. Por defecto: gemini-2.0-flash.
          </p>
        </div>
        <div className="space-y-1">
          <Label htmlFor="ft-model">Modelo fine-tuneado (opcional)</Label>
          <Input
            id="ft-model"
            value={fineTunedModel}
            onChange={(e) => setFineTunedModel(e.target.value)}
            placeholder="tunedModels/…"
          />
          <p className="text-xs text-zinc-500 dark:text-[color:var(--aurora-cream-dim)]">
            ID de un modelo tuneado en Vertex AI / Gemini Tuning. Déjalo vacío si no aplica.
          </p>
        </div>
      </div>

      <label className="inline-flex items-center gap-2 text-sm dark:text-[color:var(--aurora-cream)]">
        <input
          type="checkbox"
          checked={useFineTuned}
          onChange={(e) => setUseFineTuned(e.target.checked)}
        />
        Usar modelo fine-tuneado para nuevas evaluaciones (A/B)
      </label>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" onClick={save} disabled={pending}>
          {pending ? "Guardando…" : "Guardar"}
        </Button>
        {ok ? (
          <span className="text-xs text-emerald-600 dark:text-emerald-300">
            Guardado.
          </span>
        ) : null}
        {error ? (
          <span className="text-xs text-rose-600 dark:text-rose-300">
            {error}
          </span>
        ) : null}
      </div>
    </div>
  );
}
