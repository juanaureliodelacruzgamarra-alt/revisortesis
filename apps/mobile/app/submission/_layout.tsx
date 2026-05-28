import { Stack } from "expo-router";

export default function SubmissionLayout() {
  return (
    <Stack
      screenOptions={{
        headerBackTitle: "Atrás",
        headerStyle: { backgroundColor: "#fafafa" },
        headerTintColor: "#0f172a",
      }}
    />
  );
}
