import { cn } from "@/lib/utils";

interface ScoreRingProps {
  score: number;
  label: string;
  color: "indigo" | "violet";
}

const colorMap = {
  indigo: {
    ring: "#4f46e5",
    track: "#e0e7ff",
    text: "text-indigo-700",
    sub: "text-indigo-400",
  },
  violet: {
    ring: "#7c3aed",
    track: "#ede9fe",
    text: "text-violet-700",
    sub: "text-violet-400",
  },
};

export function ScoreRing({ score, label, color }: ScoreRingProps) {
  const radius = 36;
  const strokeWidth = 6;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const c = colorMap[color];

  return (
    <div className="flex flex-col items-center gap-2.5">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 84 84">
          <circle
            cx="42" cy="42" r={radius}
            fill="none" stroke={c.track} strokeWidth={strokeWidth}
          />
          <circle
            cx="42" cy="42" r={radius}
            fill="none" stroke={c.ring} strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-2xl font-bold", c.text)}>{score}</span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-semibold text-gray-700">{label}</p>
        <p className={cn("text-xs", c.sub)}>out of 100</p>
      </div>
    </div>
  );
}
