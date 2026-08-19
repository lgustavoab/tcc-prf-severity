const integerFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const percentFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const metricFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 4,
});

export const formatInteger = (value: number): string => integerFormatter.format(value);
export const formatPercent = (value: number): string => percentFormatter.format(value);
export const formatMetric = (value: number): string => metricFormatter.format(value);
export const formatYear = (value: number): string => String(value);
