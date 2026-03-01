import { ReactNode } from "react";

interface PageHeaderProps {
  icon: string;
  title: string;
  description?: string;
  children?: ReactNode;
}

export default function PageHeader({ icon, title, description, children }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary">
          <span className="material-symbols-outlined icon-lg">{icon}</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
        </div>
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
