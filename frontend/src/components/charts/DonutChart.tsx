"use client";

interface Slice {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: Slice[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string;
}

export default function DonutChart({ data, size = 200, thickness = 35, centerLabel, centerValue }: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) return <div className="text-gray-400 text-sm text-center py-8">Aucune donnee</div>;

  const radius = (size - thickness) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;

  return (
    <div className="flex flex-col items-center gap-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {data.filter(d => d.value > 0).map((slice, i) => {
          const pct = slice.value / total;
          const dashLength = pct * circumference;
          const dashOffset = -offset * circumference;
          offset += pct;

          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={radius}
              fill="none"
              stroke={slice.color}
              strokeWidth={thickness}
              strokeDasharray={`${dashLength} ${circumference - dashLength}`}
              strokeDashoffset={dashOffset}
              transform={`rotate(-90 ${cx} ${cy})`}
              style={{ transition: "stroke-dasharray 0.5s ease" }}
            />
          );
        })}
        {centerValue && (
          <>
            <text x={cx} y={cy - 8} textAnchor="middle" className="text-2xl font-bold" fill="#1e293b" fontSize="28">{centerValue}</text>
            {centerLabel && <text x={cx} y={cy + 14} textAnchor="middle" fill="#94a3b8" fontSize="12">{centerLabel}</text>}
          </>
        )}
      </svg>
      <div className="flex flex-wrap justify-center gap-3">
        {data.filter(d => d.value > 0).map((slice, i) => (
          <div key={i} className="flex items-center gap-1.5 text-xs">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: slice.color }} />
            <span className="text-gray-600">{slice.label}</span>
            <span className="font-bold">{slice.value}</span>
            <span className="text-gray-400">({Math.round(slice.value / total * 100)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
