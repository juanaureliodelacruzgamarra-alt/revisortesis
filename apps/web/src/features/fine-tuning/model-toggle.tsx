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

export function ModelToggle({ pref }: { pref: ModelPreference }) {
  const [openaiModel, setOpenaiModel] = useState(pref.openai_model);
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
        openai_model: openaiModel,
        fine_tuned_model: fineTunedModel || null,
        use_fine_tuned: useFineTuned,
      });
      if (!result.ok) setError(result.error);
      else setOk(true);
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Badge variant={pref.use_fine_tuned ? "success" : "muted"}>
          Activo:{" "}
          {pref.use_fine_tuned && pref.fine_tuned_model
            ? pref.fine_tuned_model
            : pref.openai_model}
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor="base-model">Modelo base</Label>
          <Input
            id="base-model"
            value={openaiModel}
            onChange={(e) => setOpenaiModel(e.target.value)}
          />
          <p className="text-xs text-zinc-500">Ej: gpt-4o-mini</p>
        </div>
        <div className="space-y-1">
          <Label htmlFor="ft-model">Modelo fine-tuneado</Label>
          <Input
            id="ft-model"
            value={fineTunedModel}
            onChange={(e) => setFineTunedModel(e.target.value)}
            placeholder="ft:gpt-4o-mini-2024-…"
          />
          <p className="text-xs text-zinc-500">
            ID devuelto por OpenAI cuando un job termina en estado succeeded.
          </p>
        </div>
      </div>

      <label className="inline-flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={useFineTuned}
          onChange={(e) => setUseFineTuned(e.target.checked)}
        />
        Usar modelo fine-tuneado para nuevas evaluaciones (A/B)
      </label>

      <div className="flex items-center gap-3">
        <Button type="button" onClick={save} disabled={pending}>
          {pending ? "Guardando…" : "Guardar"}
        </Button>
        {ok ? (
          <span className="text-xs text-emerald-600 dark:text-emerald-400">
            Guardado.
          </span>
        ) : null}
        {error ? (
          <span className="text-xs text-rose-600 dark:text-rose-400">
            {error}
          </span>
        ) : null}
      </div>
    </div>
  );
}
