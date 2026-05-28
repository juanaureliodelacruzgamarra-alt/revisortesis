import type { ReactNode } from "react";

type Props = {
  pill: string;
  title: ReactNode;
  description: ReactNode;
  highlights?: { label: string; value: string }[];
  formTitle: string;
  formDescription: ReactNode;
  formChildren: ReactNode;
  formFooter: ReactNode;
};

export function AuthSplit({
  pill,
  title,
  description,
  highlights,
  formTitle,
  formDescription,
  formChildren,
  formFooter,
}: Props) {
  return (
    <div className="grid w-full grid-cols-1 items-center gap-8 sm:gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:gap-16">
      <section className="space-y-6 sm:space-y-8">
        <span className="aurora-pill inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[11px] font-medium uppercase tracking-[0.22em] text-[color:var(--aurora-cream)]">
          <span aria-hidden className="text-[color:var(--aurora-brass)]">
            ◆
          </span>
          {pill}
        </span>

        <h1 className="aurora-display text-4xl font-bold text-[color:var(--aurora-cream)] sm:text-5xl lg:text-[5.25rem]">
          {title}
        </h1>

        <p className="max-w-xl text-sm leading-relaxed text-[color:var(--aurora-cream-dim)] sm:text-base sm:leading-relaxed lg:text-lg">
          {description}
        </p>

        {highlights && highlights.length > 0 ? (
          <dl className="grid grid-cols-3 gap-4 border-t border-[color:rgba(196,181,253,0.18)] pt-4 max-w-xl sm:gap-6 sm:pt-6">
            {highlights.map((h) => (
              <div key={h.label} className="space-y-1">
                <dt className="text-[10px] font-medium uppercase tracking-[0.2em] text-[color:var(--aurora-cream-dim)]">
                  {h.label}
                </dt>
                <dd className="aurora-display text-xl font-semibold text-[color:var(--aurora-cream)] sm:text-2xl">
                  {h.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}
      </section>

      <section className="w-full max-w-md lg:justify-self-end">
        <div className="aurora-card rounded-2xl p-5 sm:p-6 md:p-8">
          <div className="mb-5 space-y-1.5 sm:mb-6">
            <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[color:var(--aurora-primary-soft)]">
              {/* Acceso institucional is part of the auth UI */}
            </p>
            <h2 className="aurora-display text-xl font-semibold text-[color:var(--aurora-cream)] sm:text-2xl">
              {formTitle}
            </h2>
            <p className="text-sm text-[color:var(--aurora-cream-dim)]">
              {formDescription}
            </p>
          </div>

          {formChildren}

          <div className="mt-5 border-t border-[color:rgba(196,181,253,0.15)] pt-4 text-center text-sm text-[color:var(--aurora-cream-dim)] sm:mt-6">
            {formFooter}
          </div>
        </div>
      </section>
    </div>
  );
}
