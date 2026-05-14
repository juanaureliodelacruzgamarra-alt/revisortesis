import Link from "next/link";

import { RegisterForm } from "@/features/auth/register-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata = {
  title: "Crear cuenta · KIMY",
};

export default function RegisterPage() {
  return (
    <Card>
      <CardHeader className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Sistema KIMY
        </p>
        <CardTitle>Crear cuenta</CardTitle>
        <CardDescription>
          Regístrate para comenzar a usar KIMY.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <RegisterForm />
        <p className="text-center text-sm text-zinc-500">
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
          >
            Iniciar sesión
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
