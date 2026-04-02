import { ReactNode } from "react";

interface PageHeaderProps {
  icon: string;
  title: string;
  description?: string;
  count?: number;
  loading?: boolean;
  children?: ReactNode;
}

export default function PageHeader({ icon, title, description, count, loading, children }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
          <span className="material-symbols-outlined icon-lg">{icon}</span>
        </div>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {count !== undefined && !loading && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-50 text-primary">
                {count}
              </span>
            )}
            {loading && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs text-gray-400 bg-gray-100">
                ...
              </span>
            )}
          </div>
          {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
        </div>
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
