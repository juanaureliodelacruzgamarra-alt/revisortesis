import { RoleHome } from "@/features/dashboard/role-home";

export const metadata = { title: "Estudiante · KIMY" };

export default function StudentHome() {
  return (
    <RoleHome
      expectedRole="student"
      description="Sube tus avances de tesis y revisa la retroalimentación de IA y de tu asesor."
      upcoming={[
        "Carga de avances (Fase 3)",
        "Visualización de hallazgos IA (Fase 4)",
        "Reportes y evolución de notas (Fase 8)",
        "App móvil con notificaciones push (Fase 11)",
      ]}
    />
  );
}
