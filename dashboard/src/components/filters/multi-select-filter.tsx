interface FilterOption {
  value: string;
  label: string;
}

interface MultiSelectFilterProps {
  legend: string;
  options: FilterOption[];
  selected: ReadonlySet<string>;
  onChange: (selected: Set<string>) => void;
}

export function MultiSelectFilter({ legend, options, selected, onChange }: MultiSelectFilterProps) {
  const toggle = (value: string) => {
    const next = new Set(selected);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onChange(next);
  };

  return (
    <fieldset className="multi-select">
      <legend>{legend}</legend>
      <details>
        <summary>{selected.size === 0 ? "Todas" : `${selected.size} selecionada(s)`}</summary>
        <div className="multi-select-menu">
          <button type="button" className="text-button" onClick={() => onChange(new Set())}>
            Limpar seleção
          </button>
          <div className="check-list">
            {options.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  checked={selected.has(option.value)}
                  onChange={() => toggle(option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      </details>
    </fieldset>
  );
}
