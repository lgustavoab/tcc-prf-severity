export const CHART_COLORS = {
  accent: "#176c72",
  accentLight: "#70aeb1",
  severe: "#6f5b95",
  nonSevere: "#8aa4ad",
  logistic: "#5277a3",
  randomForest: "#b07a3c",
  xgboost: "#3e8068",
  reference: "#647178",
  grid: "#d6dee2",
  text: "#34444b",
} as const;

export const MODEL_LABELS: Record<string, string> = {
  phase_4a_logistic_baseline: "Regressão Logística",
  phase_4b_random_forest_baseline: "Random Forest",
  phase_4c_xgboost_baseline: "XGBoost",
};

export const MODEL_COLORS: Record<string, string> = {
  phase_4a_logistic_baseline: CHART_COLORS.logistic,
  phase_4b_random_forest_baseline: CHART_COLORS.randomForest,
  phase_4c_xgboost_baseline: CHART_COLORS.xgboost,
};

export const PREDICTOR_LABELS: Record<string, string> = {
  uf: "UF",
  tipo_pista: "Tipo de pista",
  hour: "Hora",
  br: "BR",
  condicao_metereologica: "Condição meteorológica",
  km: "Km",
  dia_semana: "Dia da semana",
  tracado_reta: "Traçado: reta",
  tracado_declive: "Traçado: declive",
  tracado_rotatoria: "Traçado: rotatória",
  month_name: "Mês",
  uso_solo: "Uso do solo",
  sentido_via: "Sentido da via",
  tracado_curva: "Traçado: curva",
  tracado_aclive: "Traçado: aclive",
  tracado_retorno_regulamentado: "Retorno regulamentado",
  tracado_intersecao_de_vias: "Interseção de vias",
  tracado_ponte: "Ponte",
  tracado_em_obras: "Trecho em obras",
  tracado_viaduto: "Viaduto",
  tracado_desvio_temporario: "Desvio temporário",
  tracado_tunel: "Túnel",
};
