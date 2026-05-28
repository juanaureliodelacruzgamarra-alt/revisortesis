import type { UserRole } from "@/lib/auth/types";

export type NavItem = {
  href: string;
  labelKey: string;
};

export const NAV_BY_ROLE: Record<UserRole, NavItem[]> = {
  student: [
    { href: "/student", labelKey: "nav.home" },
    { href: "/student/submissions", labelKey: "nav.submissions" },
    { href: "/student/reports", labelKey: "nav.reports" },
  ],
  advisor: [
    { href: "/advisor", labelKey: "nav.home" },
    { href: "/advisor/reviews", labelKey: "nav.reviews" },
    { href: "/advisor/profile", labelKey: "nav.my_profile_orcid" },
  ],
  coordinator: [
    { href: "/coordinator", labelKey: "nav.dashboard" },
    { href: "/coordinator/templates", labelKey: "nav.pattern_docs" },
    { href: "/coordinator/submissions", labelKey: "nav.advances" },
    { href: "/coordinator/reports", labelKey: "nav.reports" },
  ],
  admin: [
    { href: "/admin", labelKey: "nav.home" },
    { href: "/admin/users", labelKey: "nav.users" },
    { href: "/admin/programs", labelKey: "nav.programs" },
    { href: "/admin/settings", labelKey: "nav.settings" },
    { href: "/admin/fine-tuning", labelKey: "nav.fine_tuning" },
  ],
};
