import { Tabs } from "expo-router";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: "#fafafa" },
        headerTitleStyle: { fontWeight: "700" },
        tabBarActiveTintColor: "#0f172a",
        tabBarInactiveTintColor: "#71717a",
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Inicio", tabBarLabel: "Inicio" }}
      />
      <Tabs.Screen
        name="submissions"
        options={{ title: "Mis avances", tabBarLabel: "Avances" }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: "Mi perfil", tabBarLabel: "Perfil" }}
      />
    </Tabs>
  );
}
