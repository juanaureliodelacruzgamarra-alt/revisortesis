import { useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { listSubmissions } from "@/lib/api";
import {
  SUBMISSION_STATUS_LABELS,
  VERSION_STATUS_LABELS,
  type SubmissionSummary,
  type VersionParsingStatus,
} from "@/lib/types";

const statusColor: Record<string, string> = {
  approved: "#10b981",
  rejected: "#ef4444",
  observed: "#f59e0b",
  in_progress: "#3b82f6",
  draft: "#a1a1aa",
};

function versionTone(s: VersionParsingStatus): string {
  if (s === "ai_completed" || s === "parsed") return "#10b981";
  if (s === "failed") return "#ef4444";
  return "#f59e0b";
}

export default function SubmissionsScreen() {
  const router = useRouter();
  const [items, setItems] = useState<SubmissionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listSubmissions();
      setItems(data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            void load();
          }}
        />
      }
      ListEmptyComponent={
        <View style={styles.empty}>
          <Text style={styles.emptyText}>
            Aún no tienes avances. Súbelos desde la versión web.
          </Text>
        </View>
      }
      renderItem={({ item }) => (
        <Pressable
          onPress={() => router.push(`/submission/${item.id}`)}
          style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
        >
          <View style={styles.row}>
            <Badge color={statusColor[item.status] ?? "#71717a"}>
              {SUBMISSION_STATUS_LABELS[item.status] ?? item.status}
            </Badge>
            {item.latest_version_status ? (
              <Badge color={versionTone(item.latest_version_status)}>
                {VERSION_STATUS_LABELS[item.latest_version_status] ??
                  item.latest_version_status}
              </Badge>
            ) : null}
            {item.latest_version_number ? (
              <Badge color="#52525b">{`v${item.latest_version_number}`}</Badge>
            ) : null}
          </View>
          <Text style={styles.title}>{item.title}</Text>
          {item.chapter ? (
            <Text style={styles.subtitle}>
              {item.chapter} · {item.program.code}
            </Text>
          ) : (
            <Text style={styles.subtitle}>{item.program.code}</Text>
          )}
        </Pressable>
      )}
    />
  );
}

function Badge({ children, color }: { children: string; color: string }) {
  return (
    <View style={[styles.badge, { borderColor: color }]}>
      <Text style={[styles.badgeText, { color }]}>{children}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, gap: 12 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  empty: { alignItems: "center", padding: 24 },
  emptyText: { color: "#71717a", fontSize: 13, textAlign: "center" },
  card: {
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
  },
  cardPressed: { backgroundColor: "#f4f4f5" },
  row: { flexDirection: "row", gap: 6, flexWrap: "wrap", marginBottom: 8 },
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  badgeText: { fontSize: 11, fontWeight: "600" },
  title: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
  subtitle: { fontSize: 12, color: "#71717a", marginTop: 2 },
});
