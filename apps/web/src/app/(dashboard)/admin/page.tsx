import { RoleHome } from "@/features/dashboard/role-home";

export const metadata = { title: "Administrador · KIMY" };

export default function AdminHome() {
  return (
    <RoleHome
      expectedRole="admin"
      description="Administra usuarios, programas, integraciones y modelos de IA."
      upcoming={[
        "Gestión de usuarios y programas (Fase 1+)",
        "Configuración de Copyleaks (Fase 5)",
        "Pipeline de fine-tuning (Fase 10)",
      ]}
    />
  );
}
