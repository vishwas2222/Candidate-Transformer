export default function LoadingSpinner({ message = 'Processing...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-5">
      {/* Ring spinner */}
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-brand-100" />
        <div className="absolute inset-0 rounded-full border-4 border-brand-600 border-t-transparent animate-spin" />
      </div>

      <div className="text-center">
        <p className="text-sm font-semibold text-slate-700">{message}</p>
        <p className="text-xs text-slate-500 mt-1">
          Parsing, normalising, and merging candidate data…
        </p>
      </div>

      {/* Progress dots */}
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
