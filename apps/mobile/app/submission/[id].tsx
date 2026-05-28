import { Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { getEvaluation, getSubmission } from "@/lib/api";
import {
  SEVERITY_LABELS,
  SUBMISSION_STATUS_LABELS,
  type AIEvaluation,
  type AIFinding,
  type FindingSeverity,
  type SubmissionDetail,
} from "@/lib/types";

const SEV_ORDER: FindingSeverity[] = [
  "critical",
  "major",
  "minor",
  "suggestion",
];

const SEV_COLOR: Record<FindingSeverity, string> = {
  critical: "#b91c1c",
  major: "#b45309",
  minor: "#52525b",
  suggestion: "#3f3f46",
};

export default function SubmissionDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [evaluation, setEvaluation] = useState<AIEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    void load(id);

    async function load(submissionId: string) {
      try {
        const detail = await getSubmission(submissionId);
        setSubmission(detail);
        const latest = detail.versions[0];
        if (latest) {
          const ev = await getEvaluation(detail.id, latest.id);
          setEvaluation(ev);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    }
  }, [id]);

  const grouped = useMemo(() => {
    const map: Record<FindingSeverity, AIFinding[]> = {
      critical: [],
      major: [],
      minor: [],
      suggestion: [],
    };
    if (!evaluation) return map;
    for (const f of evaluation.findings) {
      const sev = f.human_severity_override ?? f.severity;
      map[sev].push(f);
    }
    return map;
  }, [evaluation]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }
  if (error || !submission) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error ?? "Avance no disponible."}</Text>
      </View>
    );
  }

  const latest = submission.versions[0];

  return (
    <>
      <Stack.Screen options={{ title: submission.title.slice(0, 32) }} />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.h1}>{submission.title}</Text>
        <Text style={styles.subtitle}>
          {submission.chapter ?? "—"} · {submission.program.code}
        </Text>
        <Text style={styles.statusLine}>
          Estado:{" "}
          <Text style={styles.statusValue}>
            {SUBMISSION_STATUS_LABELS[submission.status]}
          </Text>
          {latest ? `  ·  v${latest.version_number}` : ""}
        </Text>

        {evaluation ? (
          <View style={styles.evalCard}>
            <Text style={styles.evalLabel}>Evaluación IA</Text>
            <Text style={styles.evalGrade}>
              {evaluation.decimal_grade.toFixed(2)}
              <Text style={styles.evalGradeUnit}> / 20</Text>
            </Text>
            <Text style={styles.evalPercent}>
              {evaluation.total_percentage.toFixed(1)}% de cumplimiento ·{" "}
              {evaluation.backend}/{evaluation.model}
            </Text>
            <Text style={styles.evalSummary}>{evaluation.executive_summary}</Text>

            <View style={styles.dims}>
              <Dim label="Estructura" v={evaluation.structure_score} />
              <Dim label="Contenido" v={evaluation.content_score} />
              <Dim label="Forma" v={evaluation.form_score} />
              <Dim label="Originalidad" v={evaluation.originality_score} />
            </View>
          </View>
        ) : (
          <View style={styles.evalCard}>
            <Text style={styles.evalLabel}>Evaluación IA</Text>
            <Text style={styles.evalSummary}>
              Aún no hay evaluación. Estado:{" "}
              {latest?.parsing_status ?? "sin versión"}.
            </Text>
          </View>
        )}

        {evaluation && evaluation.findings.length > 0 ? (
          <View>
            <Text style={styles.h2}>
              Hallazgos ({evaluation.findings.length})
            </Text>
            {SEV_ORDER.map((sev) => {
              const items = grouped[sev];
              if (items.length === 0) return null;
              return (
                <View key={sev} style={styles.section}>
                  <Text style={[styles.sectionTitle, { color: SEV_COLOR[sev] }]}>
                    {SEVERITY_LABELS[sev]} — {items.length}
                  </Text>
                  {items.map((f) => (
                    <View key={f.id} style={styles.finding}>
                      {f.section ? (
                        <Text style={styles.findingMeta}>
                          {f.section} · {f.type}
                        </Text>
                      ) : (
                        <Text style={styles.findingMeta}>{f.type}</Text>
                      )}
                      <Text style={styles.findingDesc}>{f.description}</Text>
                      {f.instruction ? (
                        <Text style={styles.findingBody}>
                          <Text style={styles.findingBodyEm}>Cómo corregir: </Text>
                          {f.instruction}
                        </Text>
                      ) : null}
                      {f.example ? (
                        <Text style={styles.findingExample}>
                          Ejemplo: {f.example}
                        </Text>
                      ) : null}
                      {f.human_action ? (
                        <Text style={styles.findingTag}>
                          Asesor: {f.human_action}
                        </Text>
                      ) : null}
                    </View>
                  ))}
                </View>
              );
            })}
          </View>
        ) : null}
      </ScrollView>
    </>
  );
}

function Dim({ label, v }: { label: string; v: number }) {
  return (
    <View style={styles.dim}>
      <Text style={styles.dimLabel}>{label}</Text>
      <Text style={styles.dimValue}>{v.toFixed(0)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12, paddingBottom: 32 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24 },
  errorText: { color: "#b91c1c" },
  h1: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
  h2: { fontSize: 18, fontWeight: "600", color: "#0f172a", marginBottom: 8 },
  subtitle: { fontSize: 13, color: "#71717a" },
  statusLine: { fontSize: 13, color: "#52525b" },
  statusValue: { fontWeight: "600", color: "#0f172a" },
  evalCard: {
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginTop: 8,
  },
  evalLabel: { fontSize: 11, color: "#71717a", marginBottom: 6 },
  evalGrade: { fontSize: 32, fontWeight: "800", color: "#0f172a" },
  evalGradeUnit: { fontSize: 16, color: "#71717a", fontWeight: "400" },
  evalPercent: { fontSize: 12, color: "#52525b", marginBottom: 6 },
  evalSummary: { fontSize: 13, color: "#27272a", lineHeight: 18 },
  dims: { flexDirection: "row", justifyContent: "space-between", marginTop: 12 },
  dim: { alignItems: "center", flex: 1 },
  dimLabel: { fontSize: 10, color: "#71717a" },
  dimValue: { fontSize: 18, fontWeight: "700", color: "#0f172a", marginTop: 2 },
  section: { marginBottom: 16 },
  sectionTitle: { fontSize: 13, fontWeight: "700", marginBottom: 6 },
  finding: {
    backgroundColor: "#fff",
    borderColor: "#e4e4e7",
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  findingMeta: { fontSize: 11, color: "#71717a", marginBottom: 4 },
  findingDesc: { fontSize: 14, fontWeight: "500", color: "#0f172a", marginBottom: 6 },
  findingBody: { fontSize: 13, color: "#3f3f46", lineHeight: 18 },
  findingBodyEm: { fontWeight: "600" },
  findingExample: {
    marginTop: 6,
    fontSize: 12,
    color: "#52525b",
    fontStyle: "italic",
    backgroundColor: "#f4f4f5",
    padding: 8,
    borderRadius: 6,
  },
  findingTag: { marginTop: 8, fontSize: 11, color: "#0f766e", fontWeight: "600" },
});
