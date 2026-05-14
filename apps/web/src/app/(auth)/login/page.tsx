import Link from "next/link";

import { LoginForm } from "@/features/auth/login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata = {
  title: "Iniciar sesión · KIMY",
};

export default function LoginPage() {
  return (
    <Card>
      <CardHeader className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Sistema KIMY
        </p>
        <CardTitle>Iniciar sesión</CardTitle>
        <CardDescription>
          Accede con tu correo institucional y contraseña.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <LoginForm />
        <p className="text-center text-sm text-zinc-500">
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
          >
            Crear una
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
