const SIZE_CLASSES = {
  sm: "h-10 w-10 text-sm",
  lg: "h-16 w-16 text-xl",
} as const;

export function Avatar({
  handle,
  avatarUrl,
  size,
}: {
  handle: string;
  avatarUrl: string | null;
  size: "sm" | "lg";
}) {
  const sizeClass = SIZE_CLASSES[size];

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={`@${handle}`}
        className={`${sizeClass} shrink-0 rounded-full border border-border object-cover`}
      />
    );
  }

  return (
    <div
      className={`${sizeClass} flex shrink-0 items-center justify-center rounded-full border border-border bg-garnet-deep font-display uppercase text-accent`}
    >
      {handle.charAt(0)}
    </div>
  );
}
