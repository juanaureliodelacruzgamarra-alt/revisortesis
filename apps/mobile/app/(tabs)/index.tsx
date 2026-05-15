import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { listSubmissions } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { SubmissionSummary } from "@/lib/types";

export default function HomeScreen() {
  const { user } = useAuth();
  const [items, setItems] = useState<SubmissionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    try {
      const data = await listSubmissions();
      setItems(data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const latest = items[0];
  const pending = items.filter((s) => s.status !== "approved" && s.status !== "rejected").length;
  const latestGrade =
    latest && latest.latest_version_status === "ai_completed"
      ? null // grade lives on the evaluation, not on summary — leave blank here
      : null;

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            void load();
          }}
        />
      }
    >
      <Text style={styles.greeting}>Hola, {user?.full_name.split(" ")[0]}</Text>
      <Text style={styles.helper}>
        Aquí ves un resumen de tus avances. Toca "Avances" para ver el detalle
        de cada uno.
      </Text>

      <View style={styles.grid}>
        <Stat label="Avances totales" value={items.length} />
        <Stat label="En proceso" value={pending} tone="warning" />
        <Stat
          label="Último avance"
          value={latest?.title.slice(0, 24) ?? "—"}
          small
        />
      </View>

      {latest ? (
        <View style={styles.latestCard}>
          <Text style={styles.cardLabel}>Última actualización</Text>
          <Text style={styles.cardTitle}>{latest.title}</Text>
          <Text style={styles.cardSubtitle}>
            {latest.chapter ?? "—"} · {latest.program.code}
          </Text>
          <Text style={styles.cardMeta}>
            Estado: {latest.status} · Última versión:{" "}
            {latest.latest_version_number ?? "—"}
          </Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

function Stat({
  label,
  value,
  tone = "default",
  small = false,
}: {
  label: string;
  value: string | number;
  tone?: "default" | "warning";
  small?: boolean;
}) {
  return (
    <View style={styles.statBox}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text
        style={[
          styles.statValue,
          small && styles.statValueSmall,
          tone === "warning" && { color: "#b45309" },
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  greeting: { fontSize: 24, fontWeight: "700", color: "#0f172a" },
  helper: { fontSize: 13, color: "#52525b" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  statBox: {
    flexBasis: "31%",
    flexGrow: 1,
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
  },
  statLabel: { fontSize: 11, color: "#71717a", marginBottom: 4 },
  statValue: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
  statValueSmall: { fontSize: 14, fontWeight: "600" },
  latestCard: {
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 16,
  },
  cardLabel: { fontSize: 11, color: "#71717a", marginBottom: 4 },
  cardTitle: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
  cardSubtitle: { fontSize: 13, color: "#52525b", marginTop: 2 },
  cardMeta: { fontSize: 12, color: "#71717a", marginTop: 6 },
});
