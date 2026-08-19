interface YearSelectProps {
  id: string;
  label: string;
  years: number[];
  value: number | "all";
  onChange: (value: number | "all") => void;
}

export function YearSelect({ id, label, years, value, onChange }: YearSelectProps) {
  return (
    <label className="select-control" htmlFor={id}>
      <span>{label}</span>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value === "all" ? "all" : Number(event.target.value))}
      >
        <option value="all">Todos os anos</option>
        {years.map((year) => (
          <option key={year} value={year}>{year}</option>
        ))}
      </select>
    </label>
  );
}
