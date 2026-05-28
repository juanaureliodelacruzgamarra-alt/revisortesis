"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

type Lang = "es" | "en";

type Translations = Record<string, Record<Lang, string>>;

const DICT: Translations = {
  // ---- Sidebar ----
  "sidebar.title": { es: "Revisión académica con IA", en: "AI Academic Review" },
  "sidebar.logout": { es: "Cerrar sesión", en: "Log out" },

  // ---- Roles ----
  "role.admin": { es: "Administrador", en: "Administrator" },
  "role.coordinator": { es: "Coordinador", en: "Coordinator" },
  "role.advisor": { es: "Asesor", en: "Advisor" },
  "role.student": { es: "Estudiante", en: "Student" },

  // ---- Nav items ----
  "nav.home": { es: "Inicio", en: "Home" },
  "nav.programs": { es: "Programas", en: "Programs" },
  "nav.users": { es: "Usuarios", en: "Users" },
  "nav.templates": { es: "Plantillas", en: "Templates" },
  "nav.submissions": { es: "Mis avances", en: "My submissions" },
  "nav.reviews": { es: "Revisiones", en: "Reviews" },
  "nav.rubrics": { es: "Rúbricas", en: "Rubrics" },
  "nav.plagiarism": { es: "Plagio", en: "Plagiarism" },
  "nav.citations": { es: "Citas", en: "Citations" },
  "nav.settings": { es: "Configuración", en: "Settings" },
  "nav.fine_tuning": { es: "Fine-tuning", en: "Fine-tuning" },
  "nav.orcid": { es: "ORCID", en: "ORCID" },
  "nav.dashboard": { es: "Dashboard", en: "Dashboard" },
  "nav.batch": { es: "Lotes", en: "Batch" },
  "nav.pattern_docs": { es: "Documentos patrón", en: "Pattern documents" },
  "nav.advances": { es: "Avances", en: "Submissions" },
  "nav.reports": { es: "Reportes", en: "Reports" },
  "nav.my_profile_orcid": { es: "Mi perfil (ORCID)", en: "My profile (ORCID)" },

  // ---- Theme ----
  "theme.dark": { es: "Oscuro", en: "Dark" },
  "theme.light": { es: "Claro", en: "Light" },
  "lang.label": { es: "ES", en: "EN" },

  // ---- Landing page ----
  "landing.platform": { es: "Plataforma Aurelio", en: "Aurelio Platform" },
  "landing.title": { es: "Revisión inteligente de tesis", en: "Intelligent thesis review" },
  "landing.description": {
    es: "Gestión, evaluación con IA, detección de plagio y validación bibliográfica para avances académicos.",
    en: "Management, AI evaluation, plagiarism detection and bibliographic validation for academic submissions.",
  },
  "landing.login": { es: "Iniciar sesión", en: "Sign in" },
  "landing.register": { es: "Crear cuenta", en: "Create account" },

  // ---- Auth (login/register) ----
  "auth.institutional_access": { es: "Acceso institucional", en: "Institutional access" },
  "auth.email_label": { es: "Correo institucional", en: "Institutional email" },
  "auth.password_label": { es: "Contraseña", en: "Password" },
  "auth.login_title": { es: "Iniciar sesión", en: "Sign in" },
  "auth.login_desc": {
    es: "Usa tu correo institucional UNT y la contraseña que te entregó la coordinación.",
    en: "Use your UNT institutional email and the password provided by the coordination.",
  },
  "auth.login_btn": { es: "Ingresar", en: "Sign in" },
  "auth.login_pending": { es: "Ingresando…", en: "Signing in…" },
  "auth.no_account": { es: "¿No tienes cuenta?", en: "Don't have an account?" },
  "auth.create_one": { es: "Crear una", en: "Create one" },
  "auth.register_title": { es: "Crear cuenta", en: "Create account" },
  "auth.register_desc": {
    es: "Selecciona tu rol con cuidado: define qué pantallas verás y qué acciones podrás realizar.",
    en: "Choose your role carefully: it defines which screens you see and actions you can perform.",
  },
  "auth.register_btn": { es: "Crear cuenta", en: "Create account" },
  "auth.register_pending": { es: "Creando cuenta…", en: "Creating account…" },
  "auth.have_account": { es: "¿Ya tienes cuenta?", en: "Already have an account?" },
  "auth.sign_in": { es: "Iniciar sesión", en: "Sign in" },
  "auth.full_name": { es: "Nombre completo", en: "Full name" },
  "auth.role": { es: "Rol", en: "Role" },
  "auth.min_chars": { es: "Mínimo 8 caracteres.", en: "Minimum 8 characters." },
  "auth.pill_login": { es: "Revisión académica con IA", en: "AI Academic Review" },
  "auth.pill_register": { es: "Únete a la plataforma", en: "Join the platform" },
  "auth.login_title_hero": { es: "PENSAR.", en: "THINK." },
  "auth.login_title_hero2": { es: "ESCRIBIR.", en: "WRITE." },
  "auth.login_title_hero3": { es: "SUSTENTAR.", en: "DEFEND." },
  "auth.login_desc_hero": {
    es: "La plataforma donde la inteligencia artificial institucional, la validación de citas y la revisión de tu asesor convergen en una sola sesión de trabajo.",
    en: "The platform where institutional AI, citation validation, and your advisor's review converge in a single work session.",
  },
  "auth.register_title_hero1": { es: "UN PASO MÁS", en: "ONE STEP" },
  "auth.register_title_hero2": { es: "CERCA", en: "CLOSER" },
  "auth.register_title_hero3": { es: "DE TU TESIS.", en: "TO YOUR THESIS." },
  "auth.register_desc_hero": {
    es: "Crea tu cuenta para subir avances, recibir retroalimentación de la IA y trabajar en paralelo con tu asesor. La revisión queda registrada, auditada y disponible para tu jurado.",
    en: "Create your account to upload submissions, get AI feedback and work alongside your advisor. Reviews are logged, audited and available for your jury.",
  },
  "auth.highlight_findings": { es: "Hallazgos IA", en: "AI findings" },
  "auth.highlight_findings_val": { es: "6 capas", en: "6 layers" },
  "auth.highlight_citations": { es: "Citas verificadas", en: "Verified citations" },
  "auth.highlight_advisors": { es: "Asesores", en: "Advisors" },
  "auth.highlight_structure": { es: "Estructura", en: "Structure" },
  "auth.highlight_plagiarism": { es: "Plagio", en: "Plagiarism" },
  "auth.highlight_roles": { es: "Roles", en: "Roles" },
  "auth.nav_review": { es: "Revisión", en: "Review" },
  "auth.nav_evidence": { es: "Evidencia", en: "Evidence" },
  "auth.nav_rigor": { es: "Rigor", en: "Rigor" },
  "auth.support": { es: "Soporte", en: "Support" },
  "auth.footer_university": { es: "Universidad Nacional de Trujillo · Escuela de Posgrado", en: "National University of Trujillo · Graduate School" },
  "auth.footer_version": { es: "Aurelio v0.1 · Revisión académica con IA", en: "Aurelio v0.1 · AI Academic Review" },
  "auth.ai_hero_strong": { es: "inteligencia artificial institucional", en: "institutional artificial intelligence" },

  // ---- Dashboard common ----
  "dash.hello": { es: "Hola,", en: "Hello," },
  "dash.your_session": { es: "Tu sesión", en: "Your session" },
  "dash.session_desc": { es: "Información obtenida desde el backend Aurelio.", en: "Information from the Aurelio backend." },
  "dash.id": { es: "ID", en: "ID" },
  "dash.email": { es: "Correo", en: "Email" },
  "dash.role": { es: "Rol", en: "Role" },
  "dash.created": { es: "Creado", en: "Created" },
  "dash.upcoming_features": { es: "Próximas funcionalidades", en: "Upcoming features" },
  "dash.upcoming_desc": { es: "Lo que llegará a este panel en las siguientes fases.", en: "What's coming to this panel in the next phases." },

  // ---- Admin dashboard ----
  "admin.overview": { es: "Panorama del sistema en este momento.", en: "System overview at this moment." },
  "admin.users": { es: "Usuarios", en: "Users" },
  "admin.total_submissions": { es: "Avances totales", en: "Total submissions" },
  "admin.plagiarism_alerts": { es: "Alertas plagio", en: "Plagiarism alerts" },
  "admin.orcid_alerts": { es: "Alertas ORCID", en: "ORCID alerts" },
  "admin.role_distribution": { es: "Distribución por rol", en: "Role distribution" },
  "admin.role_dist_desc": { es: "Cuentas activas e inactivas combinadas.", en: "Active and inactive accounts combined." },
  "admin.manage_users": { es: "Gestionar usuarios →", en: "Manage users →" },
  "admin.ai_fine_tuning": { es: "IA y fine-tuning", en: "AI & fine-tuning" },
  "admin.ai_ft_desc": { es: "Modelo en producción y avance del entrenamiento personalizado.", en: "Production model and custom training progress." },
  "admin.active_model": { es: "Modelo activo", en: "Active model" },
  "admin.feedback_eligible": { es: "Feedback elegible", en: "Eligible feedback" },
  "admin.programmatic_tuning": { es: "Tuning programático", en: "Programmatic tuning" },
  "admin.yes": { es: "sí", en: "yes" },
  "admin.no": { es: "no", en: "no" },
  "admin.adjust_settings": { es: "Ajustar configuración →", en: "Adjust settings →" },
  "admin.view_pipeline": { es: "Ver pipeline →", en: "View pipeline →" },
  "admin.quick_links": { es: "Accesos rápidos", en: "Quick links" },
  "admin.link_users": { es: "Crear o desactivar usuarios", en: "Create or deactivate users" },
  "admin.link_programs": { es: "Administrar programas académicos", en: "Manage academic programs" },
  "admin.link_settings": { es: "Configuración del sistema", en: "System settings" },
  "admin.link_pipeline": { es: "Pipeline de fine-tuning", en: "Fine-tuning pipeline" },
  "admin.programs_count": { es: "programas", en: "programs" },

  // ---- Coordinator dashboard ----
  "coord.title": { es: "Coordinador", en: "Coordinator" },
  "coord.desc": {
    es: "KPIs agregados de todos los programas. Descarga el reporte ejecutivo para imprimir o compartir con la dirección de escuela.",
    en: "Aggregated KPIs for all programs. Download the executive report to print or share with the school board.",
  },
  "coord.exec_report": { es: "Reporte ejecutivo (PDF)", en: "Executive report (PDF)" },
  "coord.avg_ai_grade": { es: "Nota IA promedio", en: "Average AI grade" },
  "coord.compliance": { es: "de cumplimiento", en: "compliance" },
  "coord.ai_human_concordance": { es: "Concordancia IA-Humano", en: "AI-Human concordance" },
  "coord.concordance_helper": { es: "% de hallazgos aceptados sin modificar", en: "% of findings accepted without modification" },
  "coord.advisors_orcid": { es: "Asesores con ORCID", en: "Advisors with ORCID" },
  "coord.plagiarism_alerts": { es: "Alertas de plagio", en: "Plagiarism alerts" },
  "coord.plagiarism_helper": { es: "similitud ≥ 85% intra-programa", en: "similarity ≥ 85% intra-program" },
  "coord.orcid_fit_alerts": { es: "Alertas ORCID fit", en: "ORCID fit alerts" },
  "coord.orcid_fit_helper": { es: "asesor↔tesis poco afín", en: "low advisor↔thesis affinity" },
  "coord.low_compliance": { es: "Bajo cumplimiento", en: "Low compliance" },
  "coord.low_compliance_helper": { es: "< 60% en evaluación IA", en: "< 60% in AI evaluation" },
  "coord.problematic_citations": { es: "Citas problemáticas", en: "Problematic citations" },
  "coord.citations_of": { es: "de", en: "of" },
  "coord.citations_extracted": { es: "extraídas", en: "extracted" },
  "coord.status_distribution": { es: "Distribución por estado", en: "Status distribution" },
  "coord.status_dist_desc": { es: "Cantidad de avances en cada etapa del flujo.", en: "Number of submissions at each stage." },
  "coord.avg_grade_program": { es: "Nota IA promedio por programa", en: "Average AI grade per program" },
  "coord.avg_grade_desc": { es: "Promedio de la última evaluación IA por avance, sobre 20.", en: "Average of the last AI evaluation per submission, out of 20." },
  "coord.recent_activity": { es: "Actividad reciente", en: "Recent activity" },
  "coord.recent_events": { es: "Últimos eventos relevantes.", en: "Latest relevant events." },
  "coord.no_activity": { es: "Sin actividad reciente.", en: "No recent activity." },

  // ---- Student dashboard ----
  "student.desc": {
    es: "Sube tus avances, revisa los hallazgos de la IA y atiende las observaciones del asesor.",
    en: "Upload your submissions, review AI findings, and address your advisor's observations.",
  },
  "student.total_submissions": { es: "Avances totales", en: "Total submissions" },
  "student.in_progress": { es: "En proceso", en: "In progress" },
  "student.observed": { es: "Observados", en: "Observed" },
  "student.approved": { es: "Aprobados", en: "Approved" },
  "student.recent": { es: "Últimos avances", en: "Recent submissions" },
  "student.recent_desc": { es: "Tus 3 entregas más recientes. El detalle muestra hallazgos IA y citaciones.", en: "Your 3 most recent submissions. Details show AI findings and citations." },
  "student.new_submission": { es: "Nuevo avance", en: "New submission" },
  "student.no_submissions": { es: "Aún no tienes avances. Crea el primero con el botón de arriba.", en: "No submissions yet. Create your first one with the button above." },
  "student.view_all": { es: "Ver todos los avances", en: "View all submissions" },
  "student.how_it_works": { es: "¿Cómo funciona?", en: "How does it work?" },
  "student.step1": { es: "Crea un avance indicando programa, título y capítulo.", en: "Create a submission indicating program, title, and chapter." },
  "student.step2": { es: "Sube el archivo Word/PDF de tu avance.", en: "Upload your Word/PDF submission file." },
  "student.step3": { es: "Aurelio analiza estructura, contenido, citas y plagio.", en: "Aurelio analyzes structure, content, citations, and plagiarism." },
  "student.step4": { es: "Tu asesor valida los hallazgos. Recibes una notificación cuando hay cambios.", en: "Your advisor validates the findings. You receive a notification when there are changes." },

  // ---- Advisor dashboard ----
  "advisor.desc": {
    es: "Aquí tienes el resumen de los avances que te corresponden revisar.",
    en: "Here is the summary of submissions assigned to you for review.",
  },
  "advisor.assigned": { es: "Asignados", en: "Assigned" },
  "advisor.pending": { es: "Pendientes", en: "Pending" },
  "advisor.orcid_fit_alert": { es: "Alerta ORCID fit", en: "ORCID fit alert" },
  "advisor.affinity_helper": { es: "afinidad temática baja", en: "low topic affinity" },
  "advisor.to_review": { es: "Por revisar", en: "To review" },
  "advisor.to_review_desc": { es: "Avances activos asignados a ti.", en: "Active submissions assigned to you." },
  "advisor.no_pending": {
    es: "No hay avances pendientes. Cuando un estudiante suba una nueva versión, aparecerá aquí.",
    en: "No pending submissions. When a student uploads a new version, it will appear here.",
  },
  "advisor.view_all_reviews": { es: "Ver todas las revisiones →", en: "View all reviews →" },
  "advisor.my_orcid_profile": { es: "Mi perfil ORCID →", en: "My ORCID profile →" },

  // ---- Submission row ----
  "submission.no_versions": { es: "Sin versiones", en: "No versions" },
  "submission.created": { es: "Creado", en: "Created" },

  // ---- Status labels ----
  "status.draft": { es: "Borrador", en: "Draft" },
  "status.in_progress": { es: "En proceso", en: "In progress" },
  "status.observed": { es: "Observado", en: "Observed" },
  "status.approved": { es: "Aprobado", en: "Approved" },
  "status.rejected": { es: "Rechazado", en: "Rejected" },

  // ---- Charts ----
  "chart.no_submissions": { es: "Sin avances registrados aún.", en: "No submissions registered yet." },
  "chart.no_grades": { es: "Aún no hay calificaciones IA registradas.", en: "No AI grades registered yet." },
  "chart.avg_grade": { es: "Nota IA promedio", en: "Average AI grade" },
  "chart.submissions": { es: "Avances", en: "Submissions" },

  // ---- Mobile sidebar ----
  "sidebar.menu": { es: "Menú", en: "Menu" },
  "sidebar.close": { es: "Cerrar menú", en: "Close menu" },
};

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nCtx>({
  lang: "es",
  setLang: () => {},
  t: (k) => k,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("kimy-lang") as Lang) || "es";
    }
    return "es";
  });

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem("kimy-lang", l);
    document.documentElement.lang = l;
  }, []);

  const t = useCallback(
    (key: string) => DICT[key]?.[lang] ?? key,
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}
