import type { ExploratoryCounts } from "@/types/dashboard";

export interface DisplayAggregate extends ExploratoryCounts {
  label: string;
}

export function sumExploratoryCounts<T extends ExploratoryCounts>(rows: readonly T[]): ExploratoryCounts | null {
  if (rows.length === 0) return null;

  const counts = rows.reduce(
    (sum, row) => ({
      total_occurrences: sum.total_occurrences + row.total_occurrences,
      severe_occurrences: sum.severe_occurrences + row.severe_occurrences,
      non_severe_occurrences: sum.non_severe_occurrences + row.non_severe_occurrences,
    }),
    { total_occurrences: 0, severe_occurrences: 0, non_severe_occurrences: 0 },
  );

  if (counts.total_occurrences === 0) return null;
  return { ...counts, severe_proportion: counts.severe_occurrences / counts.total_occurrences };
}

export function groupExploratoryRows<T extends ExploratoryCounts>(
  rows: readonly T[],
  key: (row: T) => string,
  compare?: (left: DisplayAggregate, right: DisplayAggregate) => number,
): DisplayAggregate[] {
  const groups = new Map<string, T[]>();
  for (const row of rows) {
    const label = key(row);
    groups.set(label, [...(groups.get(label) ?? []), row]);
  }

  const aggregated = [...groups.entries()].flatMap(([label, group]) => {
    const counts = sumExploratoryCounts(group);
    return counts ? [{ label, ...counts }] : [];
  });
  return compare ? aggregated.sort(compare) : aggregated.sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
}

export const selectedOrAll = (selected: ReadonlySet<string>, value: string | number): boolean =>
  selected.size === 0 || selected.has(String(value));
