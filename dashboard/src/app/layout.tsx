import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Navigation } from "@/components/layout/navigation";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Gravidade de Acidentes em Rodovias Federais",
    template: "%s | Gravidade em Rodovias Federais",
  },
  description:
    "Análise descritiva de acidentes registrados pela PRF e avaliação de modelos de aprendizado de máquina, sem operação de previsão em tempo real.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <a className="skip-link" href="#conteudo-principal">Pular para o conteúdo principal</a>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="brand-block">
              <span className="brand-kicker">TCC · Ciência de dados</span>
              <strong>Gravidade em rodovias federais</strong>
              <span className="period-chip">PRF · 2021–2025</span>
            </div>
            <Navigation />
            <p className="sidebar-note">Publicação estática de resultados científicos e agregações descritivas.</p>
          </aside>
          <div className="content-shell">
            <main id="conteudo-principal" tabIndex={-1}>{children}</main>
            <footer>
              <span>Projeto acadêmico · dados públicos da PRF</span>
              <span>Período analisado: 2021–2025</span>
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
