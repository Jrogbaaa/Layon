import { Nav } from "@/app/components/Nav";
import { LanguageProvider } from "@/app/components/LanguageProvider";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <div className="flex min-h-full flex-1 flex-col bg-canvas text-ink">
        <Nav />
        <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">{children}</main>
      </div>
    </LanguageProvider>
  );
}
