export type UserRole = "student" | "advisor" | "coordinator" | "admin";

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type RegisterPayload = {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export const ROLE_LABELS: Record<UserRole, string> = {
  student: "Estudiante",
  advisor: "Asesor",
  coordinator: "Coordinador",
  admin: "Administrador",
};

export const ROLE_HOMES: Record<UserRole, string> = {
  student: "/student",
  advisor: "/advisor",
  coordinator: "/coordinator",
  admin: "/admin",
};
