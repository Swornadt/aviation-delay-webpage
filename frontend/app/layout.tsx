import "./globals.css";

export const metadata = {
  title: "Aviation Control Tower",
  description: "Real-time aviation analytics dashboard & RAG copilot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen">{children}</body>
    </html>
  );
}
