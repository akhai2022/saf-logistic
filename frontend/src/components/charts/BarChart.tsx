"use client";

interface BarData {
  label: string;
  value: number;
  value2?: number;
  color?: string;
}

interface BarChartProps {
  data: BarData[];
  height?: number;
  color1?: string;
  color2?: string;
  label1?: string;
  label2?: string;
  formatValue?: (n: number) => string;
}

export default function BarChart({
  data, height = 200, color1 = "#3b82f6", color2 = "#ef4444",
  label1 = "Valeur", label2, formatValue = (n) => String(n),
}: BarChartProps) {
  if (data.length === 0) return <div className="text-gray-400 text-sm text-center py-8">Aucune donnee</div>;

  const padding = { top: 20, right: 20, bottom: 40, left: 60 };
  const width = 600;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxVal = Math.max(...data.flatMap(d => [d.value, d.value2 || 0]), 1);
  const barGroupW = chartW / data.length;
  const barW = data[0]?.value2 !== undefined ? barGroupW * 0.35 : barGroupW * 0.6;
  const gap = data[0]?.value2 !== undefined ? 2 : 0;

  const toY = (v: number) => padding.top + chartH - (v / maxVal) * chartH;
  const barH = (v: number) => (v / maxVal) * chartH;

  const yTicks = 4;
  const yStep = maxVal / yTicks;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="xMidYMid meet">
        {/* Grid */}
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const y = toY(i * yStep);
          return (
            <g key={i}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#f1f5f9" strokeWidth="1" />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="10">{formatValue(Math.round(i * yStep))}</text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((d, i) => {
          const groupX = padding.left + i * barGroupW;
          const hasTwo = d.value2 !== undefined;
          return (
            <g key={i}>
              <rect
                x={hasTwo ? groupX + (barGroupW - barW * 2 - gap) / 2 : groupX + (barGroupW - barW) / 2}
                y={toY(d.value)}
                width={barW}
                height={barH(d.value)}
                rx="3"
                fill={d.color || color1}
                opacity="0.85"
              />
              {hasTwo && (
                <rect
                  x={groupX + (barGroupW - barW * 2 - gap) / 2 + barW + gap}
                  y={toY(d.value2!)}
                  width={barW}
                  height={barH(d.value2!)}
                  rx="3"
                  fill={color2}
                  opacity="0.85"
                />
              )}
              <text x={groupX + barGroupW / 2} y={height - 8} textAnchor="middle" fill="#94a3b8" fontSize="9">
                {data.length > 12 && i % 2 !== 0 ? "" : d.label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex justify-center gap-4 mt-2">
        <div className="flex items-center gap-1.5 text-xs">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color1 }} />
          <span className="text-gray-500">{label1}</span>
        </div>
        {label2 && data[0]?.value2 !== undefined && (
          <div className="flex items-center gap-1.5 text-xs">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color2 }} />
            <span className="text-gray-500">{label2}</span>
          </div>
        )}
      </div>
    </div>
  );
}
