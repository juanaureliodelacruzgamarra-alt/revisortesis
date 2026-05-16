import Link from "next/link";

import { AuthSplit } from "@/features/auth/auth-split";
import { LoginForm } from "@/features/auth/login-form";

export const metadata = {
  title: "Iniciar sesión · Aurelio",
};

export default function LoginPage() {
  return (
    <AuthSplit
      pill="Revisión académica con IA"
      title={
        <>
          PENSAR. <span className="aurora-gradient-text">ESCRIBIR.</span>
          <br />
          SUSTENTAR.
        </>
      }
      description={
        <>
          La plataforma donde la <strong className="text-[color:var(--aurora-cream)]">inteligencia artificial institucional</strong>,
          la validación de citas y la revisión de tu asesor convergen en una sola sesión de trabajo.
        </>
      }
      highlights={[
        { label: "Hallazgos IA", value: "6 capas" },
        { label: "Citas verificadas", value: "CrossRef" },
        { label: "Asesores", value: "ORCID" },
      ]}
      formTitle="Iniciar sesión"
      formDescription="Usa tu correo institucional UNT y la contraseña que te entregó la coordinación."
      formChildren={<LoginForm />}
      formFooter={
        <>
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-medium text-[color:var(--aurora-primary-soft)] underline-offset-4 hover:underline"
          >
            Crear una
          </Link>
        </>
      }
    />
  );
}
