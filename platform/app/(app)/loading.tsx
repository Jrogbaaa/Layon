export default function Loading() {
  return (
    <div className="animate-pulse space-y-12">
      {/* Masthead Skeleton */}
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div className="space-y-3">
          <div className="h-10 w-48 rounded bg-surface-2 sm:h-12" />
          <div className="h-4 w-72 rounded bg-surface" />
        </div>
        <div className="flex gap-10">
          <div className="space-y-2">
            <div className="h-3 w-12 rounded bg-surface-2" />
            <div className="h-6 w-20 rounded bg-surface" />
          </div>
          <div className="space-y-2">
            <div className="h-3 w-12 rounded bg-surface-2" />
            <div className="h-6 w-24 rounded bg-surface" />
          </div>
        </div>
      </div>

      <hr className="rule-gold mt-8 mb-10" />

      {/* Grid panels skeleton */}
      <div className="grid gap-12 lg:grid-cols-[7fr_5fr]">
        <div className="space-y-4">
          <div className="h-4 w-28 rounded bg-surface-2" />
          <div className="h-20 w-full rounded bg-surface" />
        </div>
        <div className="space-y-4">
          <div className="h-4 w-24 rounded bg-surface-2" />
          <div className="space-y-2">
            <div className="h-4 w-full rounded bg-surface" />
            <div className="h-4 w-3/4 rounded bg-surface" />
          </div>
        </div>
      </div>

      {/* Table Index list skeleton */}
      <div className="space-y-4">
        <div className="h-4 w-36 rounded bg-surface-2" />
        <div className="panel divide-y divide-border-faint overflow-hidden">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-x-4 px-5 py-4 sm:px-7">
              <div className="h-4 w-6 rounded bg-surface" />
              <div className="h-10 w-10 shrink-0 rounded-full bg-surface-2" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 rounded bg-surface" />
                <div className="h-3 w-20 rounded bg-surface" />
              </div>
              <div className="h-5 w-24 rounded bg-surface sm:w-32" />
              <div className="hidden h-5 w-24 rounded bg-surface sm:block" />
              <div className="hidden h-8 w-28 rounded bg-surface-2 sm:block" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
