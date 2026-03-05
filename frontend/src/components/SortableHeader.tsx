interface SortableHeaderProps {
  label: string;
  field: string;
  currentSort?: string;
  currentOrder?: "asc" | "desc";
  onSort: (field: string) => void;
}

export default function SortableHeader({ label, field, currentSort, currentOrder, onSort }: SortableHeaderProps) {
  const isActive = currentSort === field;

  return (
    <th
      className="cursor-pointer select-none hover:bg-gray-100 transition-colors"
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <span className={`material-symbols-outlined text-xs ${isActive ? "text-primary" : "text-gray-300"}`}>
          {isActive && currentOrder === "asc" ? "arrow_upward" : "arrow_downward"}
        </span>
      </span>
    </th>
  );
}
