export default function ProbabilityBar({ percentageString, colorClass }) {
  //extract the numeric value from strings
  const numericValue = parseFloat(percentageString.replace('%', ''));
  const width = `${numericValue}%`;

  //for very small percentages I ensure a tiny sliver is visible or hide it if exactly 0
  const isZero = numericValue === 0;

  return (
    <div className="flex items-center gap-2">
      <div className="w-12 text-right text-xs font-medium text-slate-300">
        {percentageString}
      </div>
      <div className="h-2 flex-1 rounded-sm bg-slate-800 overflow-hidden">
        {!isZero && (
          <div 
            className={`h-full rounded-sm ${colorClass}`} 
            style={{ width }} 
          />
        )}
      </div>
    </div>
  );
}