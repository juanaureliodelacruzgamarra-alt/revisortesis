import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useAuth } from "@/lib/auth";

export default function ProfileScreen() {
  const { user, signOut } = useAuth();

  if (!user) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  function onSignOut() {
    Alert.alert("Cerrar sesión", "¿Salir de tu cuenta?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Salir",
        style: "destructive",
        onPress: () => {
          void signOut();
        },
      },
    ]);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.card}>
        <Text style={styles.label}>Nombre</Text>
        <Text style={styles.value}>{user.full_name}</Text>

        <View style={styles.divider} />

        <Text style={styles.label}>Correo</Text>
        <Text style={styles.value}>{user.email}</Text>

        <View style={styles.divider} />

        <Text style={styles.label}>Rol</Text>
        <Text style={styles.value}>{user.role}</Text>

        <View style={styles.divider} />

        <Text style={styles.label}>Cuenta creada</Text>
        <Text style={styles.value}>
          {new Date(user.created_at).toLocaleDateString("es-PE")}
        </Text>
      </View>

      <Pressable
        onPress={onSignOut}
        style={({ pressed }) => [styles.logout, pressed && styles.logoutPressed]}
      >
        <Text style={styles.logoutText}>Cerrar sesión</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 16,
  },
  label: { fontSize: 11, color: "#71717a", marginBottom: 4 },
  value: { fontSize: 15, color: "#0f172a", marginBottom: 12 },
  divider: { height: 1, backgroundColor: "#f4f4f5", marginVertical: 4 },
  logout: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#fecaca",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
  },
  logoutPressed: { backgroundColor: "#fee2e2" },
  logoutText: { color: "#b91c1c", fontWeight: "600" },
});
