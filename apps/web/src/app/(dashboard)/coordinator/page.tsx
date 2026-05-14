import { RoleHome } from "@/features/dashboard/role-home";

export const metadata = { title: "Coordinador · KIMY" };

export default function CoordinatorHome() {
  return (
    <RoleHome
      expectedRole="coordinator"
      description="Gestiona documentos patrón, supervisa avances y revisa estadísticas del programa."
      upcoming={[
        "Carga de documentos patrón (Fase 2)",
        "Dashboard de KPIs y alertas (Fase 8)",
        "Revisión por lotes (Fase 9)",
        "Heatmap de similitud intra-programa (Fase 5)",
      ]}
    />
  );
}
