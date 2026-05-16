import Link from "next/link";

import { AuthSplit } from "@/features/auth/auth-split";
import { RegisterForm } from "@/features/auth/register-form";

export const metadata = {
  title: "Crear cuenta · Aurelio",
};

export default function RegisterPage() {
  return (
    <AuthSplit
      pill="Únete a la plataforma"
      title={
        <>
          UN PASO MÁS <br />
          <span className="aurora-gradient-text">CERCA</span> DE TU TESIS.
        </>
      }
      description={
        <>
          Crea tu cuenta para subir avances, recibir retroalimentación de la IA y trabajar en
          paralelo con tu asesor. La revisión queda registrada, auditada y disponible para tu
          jurado.
        </>
      }
      highlights={[
        { label: "Estructura", value: "APA 7" },
        { label: "Plagio", value: "pgvector" },
        { label: "Roles", value: "4" },
      ]}
      formTitle="Crear cuenta"
      formDescription="Selecciona tu rol con cuidado: define qué pantallas verás y qué acciones podrás realizar."
      formChildren={<RegisterForm />}
      formFooter={
        <>
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-medium text-[color:var(--aurora-primary-soft)] underline-offset-4 hover:underline"
          >
            Iniciar sesión
          </Link>
        </>
      }
    />
  );
}
