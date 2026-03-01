import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "success";
  size?: "sm" | "md" | "lg";
  icon?: string;
}

export default function Button({
  variant = "primary",
  size = "md",
  icon,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const base = "inline-flex items-center justify-center gap-1.5 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-primary text-white hover:bg-primary-700 shadow-sm",
    secondary: "bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 shadow-sm",
    danger: "bg-danger text-white hover:bg-red-700 shadow-sm",
    ghost: "text-gray-600 hover:bg-gray-100",
    success: "bg-success text-white hover:bg-green-700 shadow-sm",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const iconSizes = {
    sm: "icon-sm",
    md: "icon-sm",
    lg: "icon-md",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {icon && <span className={`material-symbols-outlined ${iconSizes[size]}`}>{icon}</span>}
      {children}
    </button>
  );
}
