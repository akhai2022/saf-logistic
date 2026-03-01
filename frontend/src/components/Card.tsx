import { ReactNode } from "react";

interface CardProps {
  title?: string;
  icon?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}

export default function Card({ title, icon, children, className = "", actions }: CardProps) {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl shadow-card hover:shadow-card-hover transition-shadow ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          {title && (
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
              {icon && <span className="material-symbols-outlined icon-md text-gray-400">{icon}</span>}
              {title}
            </h2>
          )}
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="px-6 py-4">{children}</div>
    </div>
  );
}
