import type { UserRole } from "@/lib/auth/types";

export type NavItem = {
  href: string;
  label: string;
};

export const NAV_BY_ROLE: Record<UserRole, NavItem[]> = {
  student: [
    { href: "/student", label: "Inicio" },
    { href: "/student/submissions", label: "Mis avances" },
    { href: "/student/reports", label: "Reportes" },
  ],
  advisor: [
    { href: "/advisor", label: "Inicio" },
    { href: "/advisor/reviews", label: "Revisiones" },
    { href: "/advisor/profile", label: "Mi perfil (ORCID)" },
  ],
  coordinator: [
    { href: "/coordinator", label: "Dashboard" },
    { href: "/coordinator/templates", label: "Documentos patrón" },
    { href: "/coordinator/submissions", label: "Avances" },
    { href: "/coordinator/reports", label: "Reportes" },
  ],
  admin: [
    { href: "/admin", label: "Inicio" },
    { href: "/admin/users", label: "Usuarios" },
    { href: "/admin/programs", label: "Programas" },
    { href: "/admin/settings", label: "Configuración" },
    { href: "/admin/fine-tuning", label: "Fine-tuning" },
  ],
};
