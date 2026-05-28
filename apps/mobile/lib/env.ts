import Constants from "expo-constants";

const fromEnv =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl;

export const API_URL = fromEnv ?? "http://10.0.2.2:8005";
