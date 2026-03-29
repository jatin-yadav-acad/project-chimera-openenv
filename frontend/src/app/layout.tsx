import "./globals.css";

export const metadata = {
  title: "Project Chimera | Penetration Test Environment",
  description: "Enterprise OpenEnv Vulnerability Analyzer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen border-t-4 border-blue-500">
        {children}
      </body>
    </html>
  );
}
