"use client";

import Link from "next/link";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { DATA_PATHS } from "@/lib/data/paths";
import { useDashboardAsset } from "@/lib/data/use-dashboard-asset";
import { formatInteger, formatPercent } from "@/lib/formatting/numbers";
import type { Metadata, OverviewAsset } from "@/types/dashboard";

interface ResearchQuestion {
  id: string;
  question: string;
  plainLanguage: string;
  answer: string;
  details: string[];
  caution: string;
  links: Array<{ href: string; label: string }>;
}

const RESEARCH_QUESTIONS: ResearchQuestion[] = [
  {
    id: "RQ1",
    question: "Quais características estão associadas a maiores proporções de acidentes graves entre as ocorrências registradas pela PRF?",
    plainLanguage: "Em quais contextos os casos graves representam uma parcela maior dos acidentes já registrados?",
    answer: "Entre os registros analisados, a proporção grave foi maior em Plena Noite (32,47%) do que em Pleno dia (25,30%), nos fins de semana (30,19%) do que nos dias úteis (27,33%) e em pistas simples (33,71%) do que em pistas duplas (23,35%). Também foram observadas diferenças geográficas e meteorológicas.",
    details: [
      "Na dimensão temporal, 32,47% das ocorrências registradas em Plena Noite foram graves, ante 25,30% em Pleno dia. A proporção também foi de 30,19% nos fins de semana e 27,33% nos dias úteis; entre as horas destacadas, chegou a 33,73% às 19h e a 23,12% às 8h.",
      "Geograficamente, a proporção grave foi de 35,92% no Nordeste e 24,87% no Sul. Entre os contrastes estaduais selecionados, Maranhão apresentou 45,81% e São Paulo, 18,64%. Esses percentuais descrevem a composição dos acidentes registrados em cada contexto, não a probabilidade de um acidente acontecer.",
      "Na dimensão viária, pista Simples apresentou 33,71% e pista Dupla, 23,35%. Entre condições meteorológicas informadas com pelo menos 500 ocorrências — o recorte descritivo adotado na análise — Nevoeiro/Neblina apresentou 31,50% e Garoa/Chuvisco, 22,26%.",
      "Em conjunto, os resultados mostram que a gravidade não se distribuiu da mesma forma em todos os contextos observados. Contagens respondem quantos acidentes foram registrados; proporções mostram qual parcela desses registros foi grave. Sem um denominador de exposição ao tráfego, nenhuma das duas medidas informa perigo absoluto ou permite uma interpretação causal.",
    ],
    caution: "Essas diferenças mostram padrões entre acidentes já registrados. Elas não demonstram que uma característica cause maior gravidade.",
    links: [
      { href: "/exploracao", label: "Explorar contextos" },
      { href: "/geografia", label: "Ver geografia" },
    ],
  },
  {
    id: "RQ2",
    question: "Em que medida características disponíveis no momento inicial da ocorrência permitem distinguir acidentes graves dos não graves?",
    plainLanguage: "Quanto os modelos conseguem separar casos graves e não graves usando apenas as características escolhidas para representar o momento inicial da ocorrência?",
    answer: "Os modelos encontraram informação útil nessas características, mas a capacidade de distinção foi moderada. Há padrões aproveitáveis, porém eles não permitem identificar perfeitamente todos os casos graves.",
    details: [
      "No conjunto completo, aproximadamente 28,27% das ocorrências registradas foram graves. Esse percentual descreve a frequência da classe grave na população analisada; não é, sozinho, uma medida do desempenho dos modelos.",
      "Capacidade preditiva moderada significa que existe sinal nas características selecionadas e que os modelos conseguem separar parcialmente graves e não graves. Ainda há bastante sobreposição entre os dois grupos: as informações disponíveis ajudam, mas não determinam sozinhas a gravidade de uma ocorrência.",
      "As características foram escolhidas por serem conceitualmente compatíveis com o cenário do início da ocorrência. O conjunto público, porém, não registra o instante em que cada campo foi preenchido, e esta pesquisa não validou sua disponibilidade real no fluxo operacional da PRF.",
    ],
    caution: "A compatibilidade das variáveis com o momento inicial é uma premissa metodológica. O fluxo interno da PRF e o instante real de preenchimento de cada campo não foram validados.",
    links: [{ href: "/modelos", label: "Entender os modelos" }],
  },
  {
    id: "RQ3",
    question: "Como Regressão Logística, Random Forest e XGBoost se comparam em validação temporal?",
    plainLanguage: "Qual dos três modelos ficou em primeiro pela regra definida e quão diferentes foram os resultados?",
    answer: "O XGBoost apresentou a maior Average Precision (AP), métrica usada aqui para avaliar o quanto o modelo consegue priorizar os casos graves ao longo de diferentes limiares. Quanto maior a AP, melhor o desempenho nesse critério: XGBoost 0,4008, Random Forest 0,3960 e Regressão Logística 0,3935.",
    details: [
      "A comparação reuniu três famílias: Regressão Logística como modelo de referência mais simples, Random Forest como conjunto de árvores e XGBoost como árvores construídas sequencialmente. Elas foram avaliadas nas mesmas validações temporais.",
      "As APs médias foram 0,3935 para Regressão Logística, 0,3960 para Random Forest e 0,4008 para XGBoost. As diferenças médias foram aproximadamente 0,0025 entre Random Forest e Logística, 0,0073 entre XGBoost e Logística e 0,0048 entre XGBoost e Random Forest.",
      "A regra definida antes da avaliação final selecionava a maior Average Precision média, por isso o XGBoost ficou em primeiro. As distâncias absolutas foram pequenas e não sustentam afirmar que uma família foi amplamente melhor que as demais ou que essa ordenação seja universal.",
    ],
    caution: "O XGBoost ficou em primeiro lugar pela regra definida, mas as diferenças absolutas entre os modelos foram pequenas.",
    links: [{ href: "/modelos", label: "Comparar os modelos" }],
  },
  {
    id: "RQ4",
    question: "O desempenho preditivo permanece consistente entre diferentes anos de validação?",
    plainLanguage: "Os modelos mantiveram comportamento semelhante quando avaliados em 2022, 2023 e 2024?",
    answer: "Os resultados dos três anos de validação ficaram relativamente próximos, sem mudanças abruptas no desempenho.",
    details: [
      "O desenho respeitou a ordem do tempo: na primeira validação, o modelo aprendeu com 2021 e foi testado em 2022; na segunda, aprendeu com 2021–2022 e foi testado em 2023; na terceira, aprendeu com 2021–2023 e foi testado em 2024.",
      "Em linguagem simples, o modelo aprende com o passado e é testado em um período posterior. Para este objetivo, essa separação é mais coerente do que misturar aleatoriamente registros de todos os anos, pois evita que o treinamento receba exemplos do futuro em relação à validação.",
      "No XGBoost, a AP variou aproximadamente de 0,3904 a 0,4071 entre as três validações. Os resultados não apresentaram mudança abrupta, mas o período e o volume de treinamento aumentam enquanto o ano avaliado também muda; por isso, a sequência não demonstra tendência temporal de melhora.",
    ],
    caution: "O volume e o período usados no treinamento e o ano de validação mudam ao mesmo tempo. A sequência não demonstra uma tendência temporal de melhora.",
    links: [{ href: "/validacao-temporal", label: "Ver as validações temporais" }],
  },
  {
    id: "RQ5",
    question: "O modelo selecionado mantém desempenho em um período temporal posterior, reservado para avaliação final em 2025?",
    plainLanguage: "O XGBoost continuou próximo dos resultados de desenvolvimento quando foi aplicado ao período final?",
    answer: "O desempenho em 2025 permaneceu próximo ao observado durante o desenvolvimento. Após as principais decisões de modelagem, o XGBoost foi avaliado nesse período e obteve AP 0,3974, ROC-AUC 0,6286 e Brier 0,1938.",
    details: [
      "A seleção do modelo usou as validações de 2022–2024, e o limiar de decisão foi fixado com as predições temporais autorizadas desses períodos. Depois, o XGBoost final foi ajustado com 2021–2024 e avaliado em 2025. O resultado final não alterou a seleção do modelo, sua configuração ou o limiar.",
      "A AP média do XGBoost no desenvolvimento foi 0,4008 e a AP final foi 0,3974, valores próximos no período observado. Em 2025, a ROC-AUC foi 0,6286 e o Brier, 0,1938. Para AP e ROC-AUC, valores maiores indicam melhor priorização ou distinção no respectivo critério; para Brier, valores menores indicam menor erro probabilístico.",
      "No limiar congelado de aproximadamente 0,2372, a precisão positiva foi 33,16%, a sensibilidade 77,18% e o F1 0,4639. Como aproximação pedagógica dos percentuais observados em 2025: entre 100 ocorrências realmente graves, cerca de 77 foram identificadas como graves; entre 100 classificadas pelo modelo como graves, cerca de 33 eram realmente graves.",
      "A matriz publicada registrou 20.153 verdadeiros negativos, 31.883 falsos positivos, 4.676 falsos negativos e 15.817 verdadeiros positivos. Esses números descrevem o ponto de operação no conjunto de 2025 e não constituem promessa de desempenho futuro ou validação para uso operacional.",
    ],
    caution: "A avaliação cobre um único ano final e não foi uma validação operacional. O desempenho de 2025 não foi usado para selecionar modelo ou limiar nem para ajustar decisões finais; ainda assim, esse ano já havia participado de análises exploratórias e de verificações sobre mudanças na estrutura e na distribuição dos dados.",
    links: [
      { href: "/modelos", label: "Ver avaliação de 2025" },
      { href: "/limiar", label: "Entender o limiar" },
    ],
  },
];

const TECHNICAL_TERMS = [
  ["Aprendizado de máquina", "Métodos computacionais que aprendem padrões a partir de exemplos para produzir previsões em novos registros."],
  ["Variável-alvo / target", "Resultado que o modelo procura identificar. Neste estudo, indica se a ocorrência registrada foi grave."],
  ["Variável preditora", "Informação fornecida ao modelo para formar uma previsão, como hora, UF ou tipo de pista."],
  ["Regressão Logística", "Modelo estatístico usado aqui como modelo de referência para estimar a probabilidade da classe grave."],
  ["Random Forest", "Conjunto de árvores de decisão cujas previsões são combinadas."],
  ["XGBoost", "Modelo que constrói árvores sequencialmente para corrigir erros das anteriores; foi o selecionado neste experimento."],
  ["Average Precision", "Métrica usada para avaliar o quanto o modelo consegue priorizar corretamente os casos graves ao longo de diferentes limiares. Quanto maior o valor, melhor o desempenho nesse critério."],
  ["ROC-AUC", "Resume a capacidade de ordenar e distinguir graves e não graves ao longo de diferentes limiares. Quanto maior o valor, melhor a capacidade de distinção."],
  ["Brier Score", "Neste estudo, mede o erro entre as probabilidades previstas e os resultados observados. Valores menores indicam melhor desempenho nesse critério."],
  ["Validação temporal", "Avaliação em um período posterior ao usado no treinamento, preservando a direção do tempo."],
  ["Limiar de decisão", "Valor usado para transformar uma pontuação ou probabilidade do modelo em uma decisão de classe."],
  ["Sensibilidade", "Entre todos os acidentes realmente graves, quantos foram identificados como graves."],
  ["Precisão positiva", "Entre os acidentes classificados como graves, quantos eram realmente graves."],
  ["Calibração", "Relação entre as probabilidades previstas e as proporções observadas nos dados."],
  ["SHAP", "Forma de analisar quanto cada variável contribuiu para as previsões do modelo. Não identifica causalidade."],
  ["Leakage", "Uso indevido de informação que não estaria legitimamente disponível no momento da previsão e que pode produzir avaliação artificialmente otimista."],
  ["Reprodutibilidade", "Capacidade de obter e verificar os mesmos resultados a partir do procedimento documentado."],
] as const;

const CAN_ANSWER = [
  "Diferenças descritivas de gravidade entre acidentes registrados.",
  "Associações observadas nas características analisadas.",
  "Capacidade preditiva dos modelos avaliados.",
  "Comparação entre Regressão Logística, Random Forest e XGBoost.",
  "Consistência do desempenho entre as validações temporais.",
  "Comportamento do modelo no período final de 2025.",
  "Variáveis que mais contribuíram para as previsões do modelo.",
] as const;

const CANNOT_ANSWER = [
  "Qual rodovia possui maior risco absoluto de acidente.",
  "A probabilidade de uma pessoa sofrer acidente ao trafegar por uma região.",
  "Relações de causa e efeito.",
  "Que uma UF ou BR seja mais perigosa.",
  "A eficácia de uma intervenção de segurança.",
  "Prontidão para uso operacional em tempo real.",
] as const;

export function AboutStudyFoundation() {
  const meta = useDashboardAsset<Metadata>(DATA_PATHS.meta, { assetId: "META" });
  const overview = useDashboardAsset<OverviewAsset>(DATA_PATHS.overview, { assetId: "OVERVIEW" });

  if (meta.status === "loading" || overview.status === "loading") return <LoadingState label="Carregando a apresentação do estudo…" />;
  if (meta.status === "error") return <ErrorState message={meta.error} />;
  if (overview.status === "error") return <ErrorState message={overview.error} />;

  const summary = overview.data.summary;

  return (
    <div className="about-study section-stack">
      <section className="surface about-introduction" aria-labelledby="about-introduction-title">
        <div>
          <span className="eyebrow">O trabalho em poucas palavras</span>
          <h2 id="about-introduction-title">Gravidade entre acidentes já registrados</h2>
          <p>Este trabalho analisa acidentes registrados pela Polícia Rodoviária Federal entre 2021 e 2025 para investigar quais características aparecem associadas à gravidade das ocorrências e avaliar até que ponto modelos de aprendizado de máquina conseguem distinguir acidentes graves dos não graves.</p>
          <p>O estudo examina a gravidade dentro do conjunto de acidentes registrados. Ele não estima a chance de um acidente acontecer durante uma viagem.</p>
        </div>
        <div className="about-summary-grid" aria-label="Resumo numérico do estudo">
          <article className="metric-card"><span>Ocorrências analisadas</span><strong>{formatInteger(summary.total_occurrences)}</strong></article>
          <article className="metric-card"><span>Período</span><strong>{meta.data.data_period.start_year}–{meta.data.data_period.end_year}</strong></article>
          <article className="metric-card"><span>Ocorrências graves</span><strong>{formatInteger(summary.severe_occurrences)}</strong></article>
          <article className="metric-card"><span>Proporção grave</span><strong>{formatPercent(summary.severe_proportion)}</strong></article>
        </div>
      </section>

      <section className="surface target-definition" aria-labelledby="target-definition-title">
        <div>
          <span className="eyebrow">Definição adotada neste TCC</span>
          <h2 id="target-definition-title">O que é um acidente grave?</h2>
          <p>Uma ocorrência é considerada grave quando existe pelo menos uma pessoa morta ou ferida gravemente. Essa é a definição operacional deste estudo, não uma definição universal para qualquer contexto.</p>
        </div>
        <code>{meta.data.target_definition}</code>
      </section>

      <section className="surface central-question" aria-labelledby="central-question-title">
        <span className="eyebrow">Pergunta central</span>
        <h2 id="central-question-title">O que o estudo investiga?</h2>
        <blockquote>Quais características temporais, geográficas, meteorológicas e viárias estão associadas à gravidade dos acidentes registrados em rodovias federais brasileiras e em que medida modelos de aprendizado de máquina conseguem identificar ocorrências graves?</blockquote>
        <div className="plain-language-note"><strong>Em outras palavras</strong><p>Entre os acidentes que já foram registrados pela PRF, em quais contextos uma parcela maior das ocorrências foi grave e quanto os modelos conseguem aprender com esses padrões?</p></div>
      </section>

      <section aria-labelledby="research-questions-title">
        <div className="section-heading">
          <span className="eyebrow">RQ1–RQ5</span>
          <h2 id="research-questions-title">Perguntas que o estudo procura responder</h2>
          <p>Cada resposta resume a evidência aprovada e indica onde o resultado pode ser consultado no dashboard.</p>
        </div>
        <div className="research-question-grid">
          {RESEARCH_QUESTIONS.map((item) => (
            <article className="research-question-card" key={item.id}>
              <span className="question-id">{item.id}</span>
              <h3>{item.question}</h3>
              <div className="plain-language-note"><strong>Em outras palavras</strong><p>{item.plainLanguage}</p></div>
              <p className="question-answer"><strong>Resposta curta:</strong> {item.answer}</p>
              <details className="research-question-details">
                <summary>Entenda melhor este resultado</summary>
                <div>{item.details.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</div>
              </details>
              <p className="question-caution"><strong>Ressalva:</strong> {item.caution}</p>
              <div className="inline-links">{item.links.map((link) => <Link href={link.href} key={link.href}>{link.label}<span aria-hidden="true"> →</span></Link>)}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="surface frozen-results" id="resultados-congelados" aria-labelledby="frozen-results-title">
        <span className="eyebrow">Leitura do dashboard</span>
        <h2 id="frozen-results-title">O que significa “resultado congelado”?</h2>
        <p>Alguns resultados deste dashboard foram calculados durante a execução do estudo e depois fixados. O site apenas apresenta esses valores; ele não treina novamente os modelos nem altera as métricas quando a página é aberta.</p>
        <p>Isso inclui comparação dos modelos, métricas de validação, avaliação de 2025, limiar de decisão, matriz de confusão, calibração e resultados SHAP.</p>
        <div className="frozen-explanation-grid">
          <article>
            <h3>Dados históricos analisados</h3>
            <p>São registros públicos da PRF referentes a 2021–2025 usados como recorte deste estudo. Eles não formam um feed em tempo real.</p>
          </article>
          <article>
            <h3>Resultados congelados</h3>
            <p>São saídas do experimento calculadas e posteriormente fixadas, como AP, ROC-AUC, Brier, limiar de decisão, matriz de confusão e SHAP.</p>
          </article>
        </div>
        <div className="reproducibility-note">
          <h3>Por que congelar?</h3>
          <p>Um resultado científico precisa ser reproduzível. Congelar os resultados garante que o número mostrado no dashboard seja o mesmo número avaliado, discutido e documentado no TCC. <strong>Reprodutibilidade</strong> é a capacidade de obter e verificar os mesmos resultados a partir do procedimento documentado.</p>
        </div>
      </section>

      <section className="surface exploratory-filters" aria-labelledby="exploratory-filters-title">
        <span className="eyebrow">Interatividade com limites claros</span>
        <h2 id="exploratory-filters-title">E os filtros?</h2>
        <p>As páginas Exploração e Geografia possuem filtros interativos. Esses filtros não treinam novos modelos.</p>
        <p>Eles selecionam grupos de dados já resumidos e publicados, chamados de células agregadas. O dashboard soma <code>total_occurrences</code>, <code>severe_occurrences</code> e <code>non_severe_occurrences</code> e pode calcular somente <code>severe_occurrences / total_occurrences</code>, isto é, a proporção de ocorrências graves no recorte selecionado.</p>
        <p>Em linguagem simples: os filtros servem para explorar os registros de diferentes formas, não para modificar o experimento de aprendizado de máquina.</p>
      </section>

      <section aria-labelledby="technical-terms-title">
        <div className="section-heading">
          <span className="eyebrow">Glossário de referência</span>
          <h2 id="technical-terms-title">Termos utilizados no estudo</h2>
          <p>Você não precisa memorizar esses termos. As páginas usam os conceitos técnicos porque eles fazem parte do estudo, mas esta seção serve como referência sempre que necessário.</p>
        </div>
        <dl className="technical-terms-grid">
          {TECHNICAL_TERMS.map(([term, definition]) => <div className="technical-term" key={term}><dt>{term}</dt><dd>{definition}</dd></div>)}
        </dl>
      </section>

      <section className="study-scope-grid" aria-label="Alcance científico do estudo">
        <article className="scope-card scope-card-can">
          <span className="eyebrow">Alcance</span>
          <h2>O que o estudo pode responder?</h2>
          <ul>{CAN_ANSWER.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>
        <article className="scope-card scope-card-cannot">
          <span className="eyebrow">Limites essenciais</span>
          <h2>O que o estudo não pode responder?</h2>
          <ul>{CANNOT_ANSWER.map((item) => <li key={item}>{item}</li>)}</ul>
          <p>O principal motivo é a ausência de um denominador de <strong>exposição ao tráfego</strong>: quantidade de veículos, pessoas ou quilômetros percorridos que estiveram expostos à possibilidade de acidente.</p>
        </article>
      </section>

      <section className="surface next-steps" aria-labelledby="next-steps-title">
        <span className="eyebrow">Continue a leitura</span>
        <h2 id="next-steps-title">Escolha um próximo passo</h2>
        <div className="cta-grid">
          <Link href="/visao-geral"><strong>Ver a Visão Geral</strong><span>Conheça os números anuais e o panorama do período.</span></Link>
          <Link href="/exploracao"><strong>Explorar os dados</strong><span>Explore diferentes recortes dos registros com filtros descritivos.</span></Link>
          <Link href="/modelos"><strong>Comparar os modelos</strong><span>Veja resultados congelados e a avaliação de 2025.</span></Link>
          <Link href="/metodologia"><strong>Entender a metodologia</strong><span>Consulte o desenho temporal, as variáveis e as transformações aplicadas aos dados.</span></Link>
        </div>
      </section>
    </div>
  );
}
