"use client";

interface DataPoint {
  label: string;
  value: number;
  value2?: number;
}

interface LineChartProps {
  data: DataPoint[];
  height?: number;
  color1?: string;
  color2?: string;
  label1?: string;
  label2?: string;
  formatValue?: (n: number) => string;
}

export default function LineChart({
  data, height = 200, color1 = "#3b82f6", color2 = "#ef4444",
  label1 = "Valeur", label2, formatValue = (n) => String(n),
}: LineChartProps) {
  if (data.length === 0) return <div className="text-gray-400 text-sm text-center py-8">Aucune donnee</div>;

  const padding = { top: 20, right: 20, bottom: 40, left: 60 };
  const width = 600;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const allValues = data.flatMap(d => [d.value, d.value2 || 0]);
  const maxVal = Math.max(...allValues, 1);
  const minVal = Math.min(...allValues.filter(v => v > 0), 0);

  const xStep = chartW / Math.max(data.length - 1, 1);

  const toX = (i: number) => padding.left + i * xStep;
  const toY = (v: number) => padding.top + chartH - (v / maxVal) * chartH;

  const path1 = data.map((d, i) => `${i === 0 ? "M" : "L"} ${toX(i)} ${toY(d.value)}`).join(" ");
  const area1 = `${path1} L ${toX(data.length - 1)} ${toY(0)} L ${toX(0)} ${toY(0)} Z`;

  const path2 = data[0]?.value2 !== undefined
    ? data.map((d, i) => `${i === 0 ? "M" : "L"} ${toX(i)} ${toY(d.value2 || 0)}`).join(" ")
    : null;

  // Y axis ticks
  const yTicks = 4;
  const yStep = maxVal / yTicks;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="xMidYMid meet">
        {/* Grid lines */}
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const y = toY(i * yStep);
          return (
            <g key={i}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#f1f5f9" strokeWidth="1" />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="10">
                {formatValue(Math.round(i * yStep))}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        <path d={area1} fill={color1} opacity="0.1" />

        {/* Line 1 */}
        <path d={path1} fill="none" stroke={color1} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* Line 2 */}
        {path2 && <path d={path2} fill="none" stroke={color2} strokeWidth="2" strokeDasharray="6 3" strokeLinecap="round" />}

        {/* Data points */}
        {data.map((d, i) => (
          <circle key={i} cx={toX(i)} cy={toY(d.value)} r="3" fill={color1} stroke="white" strokeWidth="1.5" />
        ))}

        {/* X axis labels */}
        {data.map((d, i) => {
          if (data.length > 15 && i % 2 !== 0) return null;
          return (
            <text key={i} x={toX(i)} y={height - 8} textAnchor="middle" fill="#94a3b8" fontSize="9">
              {d.label}
            </text>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex justify-center gap-4 mt-2">
        <div className="flex items-center gap-1.5 text-xs">
          <div className="w-4 h-0.5 rounded" style={{ backgroundColor: color1 }} />
          <span className="text-gray-500">{label1}</span>
        </div>
        {label2 && path2 && (
          <div className="flex items-center gap-1.5 text-xs">
            <div className="w-4 h-0.5 rounded border-b border-dashed" style={{ borderColor: color2 }} />
            <span className="text-gray-500">{label2}</span>
          </div>
        )}
      </div>
    </div>
  );
}
