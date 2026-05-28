import { Badge } from "@/components/ui/badge";
import {
  SUBMISSION_STATUS_LABELS,
  VERSION_STATUS_LABELS,
  type SubmissionStatus,
  type VersionParsingStatus,
} from "@/lib/api/types";

function submissionVariant(status: SubmissionStatus) {
  switch (status) {
    case "approved":
      return "success" as const;
    case "rejected":
      return "destructive" as const;
    case "observed":
      return "warning" as const;
    case "in_progress":
      return "default" as const;
    case "draft":
      return "muted" as const;
  }
}

function versionVariant(status: VersionParsingStatus) {
  switch (status) {
    case "ai_completed":
    case "parsed":
      return "success" as const;
    case "failed":
      return "destructive" as const;
    case "ai_processing":
    case "ai_queued":
    case "processing":
    case "pending":
      return "warning" as const;
  }
}

export function SubmissionStatusBadge({
  status,
}: {
  status: SubmissionStatus;
}) {
  return (
    <Badge variant={submissionVariant(status)}>
      {SUBMISSION_STATUS_LABELS[status]}
    </Badge>
  );
}

export function VersionStatusBadge({
  status,
}: {
  status: VersionParsingStatus;
}) {
  return (
    <Badge variant={versionVariant(status)}>
      {VERSION_STATUS_LABELS[status]}
    </Badge>
  );
}
