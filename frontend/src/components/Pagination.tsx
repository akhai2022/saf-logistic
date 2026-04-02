import Button from "@/components/Button";

interface PaginationProps {
  offset: number;
  limit: number;
  currentCount: number;
  onPrev: () => void;
  onNext: () => void;
}

/** Record count badge — shows above/inside tables. */
export function RecordCount({ count, loading, label }: { count: number; loading?: boolean; label?: string }) {
  if (loading) return <span className="text-xs text-gray-400">Chargement...</span>;
  const noun = label || "résultat" + (count !== 1 ? "s" : "");
  return (
    <span className="text-xs text-gray-500 font-medium">
      {count} {noun}
    </span>
  );
}

export default function Pagination({ offset, limit, currentCount, onPrev, onNext }: PaginationProps) {
  const from = offset + 1;
  const to = offset + currentCount;
  const hasMultiplePages = offset > 0 || currentCount >= limit;

  return (
    <div className="flex justify-between items-center pt-4 border-t mt-4">
      {hasMultiplePages ? (
        <>
          <Button variant="ghost" size="sm" onClick={onPrev} disabled={offset === 0} icon="chevron_left">
            Précédent
          </Button>
          <span className="text-xs text-gray-500">
            {from}–{to} · Page {Math.floor(offset / limit) + 1}
          </span>
          <Button variant="ghost" size="sm" onClick={onNext} disabled={currentCount < limit} icon="chevron_right">
            Suivant
          </Button>
        </>
      ) : (
        <span className="text-xs text-gray-400 w-full text-center">
          {currentCount} résultat{currentCount !== 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}
