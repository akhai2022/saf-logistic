import Button from "@/components/Button";

interface PaginationProps {
  offset: number;
  limit: number;
  currentCount: number;
  onPrev: () => void;
  onNext: () => void;
}

export default function Pagination({ offset, limit, currentCount, onPrev, onNext }: PaginationProps) {
  if (offset === 0 && currentCount < limit) return null;

  return (
    <div className="flex justify-between items-center pt-4 border-t mt-4">
      <Button variant="ghost" size="sm" onClick={onPrev} disabled={offset === 0} icon="chevron_left">
        Précédent
      </Button>
      <span className="text-sm text-gray-500">
        Page {Math.floor(offset / limit) + 1}
      </span>
      <Button variant="ghost" size="sm" onClick={onNext} disabled={currentCount < limit} icon="chevron_right">
        Suivant
      </Button>
    </div>
  );
}
