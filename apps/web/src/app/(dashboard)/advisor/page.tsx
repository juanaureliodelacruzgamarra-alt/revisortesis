import { RoleHome } from "@/features/dashboard/role-home";

export const metadata = { title: "Asesor · KIMY" };

export default function AdvisorHome() {
  return (
    <RoleHome
      expectedRole="advisor"
      description="Revisa los avances de tus estudiantes y valida la evaluación de IA."
      upcoming={[
        "Vincular perfil con ORCID (Fase 7)",
        "Revisión individual lado a lado (Fase 4)",
        "Feedback loop a fine-tuning (Fase 10)",
      ]}
    />
  );
}
