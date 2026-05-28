import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  ApiError,
  login as apiLogin,
  me as apiMe,
  registerPushToken,
  unregisterPushToken,
} from "@/lib/api";
import { registerForPushNotificationsAsync } from "@/lib/push";
import { clearTokens, getAccessToken, saveTokens } from "@/lib/storage";
import type { CurrentUser } from "@/lib/types";

type AuthState = {
  user: CurrentUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void bootstrap();

    async function bootstrap() {
      const token = await getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const u = await apiMe();
        setUser(u);
      } catch {
        await clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      signIn: async (email, password) => {
        const tokens = await apiLogin(email, password);
        await saveTokens(tokens.access_token, tokens.refresh_token);
        const u = await apiMe();
        setUser(u);

        // Best-effort push registration — never blocks login.
        try {
          const token = await registerForPushNotificationsAsync();
          if (token) await registerPushToken(token, "mobile");
        } catch {
          /* swallow */
        }
      },
      signOut: async () => {
        // Best-effort unregister; ignore network failures.
        try {
          const token = await registerForPushNotificationsAsync();
          if (token) await unregisterPushToken(token);
        } catch {
          /* swallow */
        }
        await clearTokens();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export type { CurrentUser };
export { ApiError };
