export type PageStatus = "MIXED" | "EXPLORATORY" | "FROZEN_RESULT" | "DOCUMENTATION";

export interface NavigationItem {
  href: string;
  label: string;
  shortLabel: string;
  status: PageStatus;
}

export const NAV_ITEMS: readonly NavigationItem[] = [
  { href: "/", label: "Visão Geral", shortLabel: "Geral", status: "MIXED" },
  { href: "/exploracao", label: "Exploração", shortLabel: "Exploração", status: "EXPLORATORY" },
  { href: "/geografia", label: "Geografia", shortLabel: "Geografia", status: "EXPLORATORY" },
  { href: "/modelos", label: "Modelos", shortLabel: "Modelos", status: "FROZEN_RESULT" },
  { href: "/validacao-temporal", label: "Validação Temporal", shortLabel: "Validação", status: "FROZEN_RESULT" },
  { href: "/limiar", label: "Limiar de Decisão", shortLabel: "Limiar", status: "FROZEN_RESULT" },
  { href: "/interpretacao", label: "Interpretação", shortLabel: "Interpretação", status: "FROZEN_RESULT" },
  { href: "/metodologia", label: "Metodologia", shortLabel: "Método", status: "DOCUMENTATION" },
] as const;
