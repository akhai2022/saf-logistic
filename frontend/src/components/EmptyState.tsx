interface EmptyStateProps {
  icon: string;
  title: string;
  description?: string;
}

export default function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <span className="material-symbols-outlined text-gray-300 mb-3" style={{ fontSize: 48 }}>
        {icon}
      </span>
      <p className="text-gray-400 font-medium">{title}</p>
      {description && <p className="text-gray-300 text-sm mt-1">{description}</p>}
    </div>
  );
}
