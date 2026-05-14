import type { TemplateSection } from "@/lib/api/types";

function Node({ section }: { section: TemplateSection }) {
  return (
    <li className="space-y-1">
      <div className="flex items-baseline gap-2">
        {section.number ? (
          <span className="font-mono text-xs text-zinc-500">{section.number}</span>
        ) : null}
        <span className="font-medium">{section.title}</span>
        <span className="text-xs text-zinc-500">
          · {section.paragraph_count} ¶ · {section.char_count} chars
        </span>
      </div>
      {section.children.length > 0 ? (
        <ul className="ml-4 space-y-1 border-l border-zinc-200 pl-4 dark:border-zinc-800">
          {section.children.map((child, idx) => (
            <Node
              key={`${child.title}-${idx}`}
              section={child}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function StructureTree({
  sections,
}: {
  sections: TemplateSection[];
}) {
  if (sections.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        No se detectaron secciones. Verifica que el documento use estilos de
        encabezado o numeración (1., 1.1, etc.).
      </p>
    );
  }
  return (
    <ul className="space-y-2 text-sm">
      {sections.map((s, idx) => (
        <Node key={`${s.title}-${idx}`} section={s} />
      ))}
    </ul>
  );
}
