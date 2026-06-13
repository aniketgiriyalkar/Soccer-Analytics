import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Football Lab | Aniket Giriyalkar",
  description:
    "Interactive player, team, match, and manager analytics across European football.",
  openGraph: {
    title: "Football Lab",
    description:
      "Detailed, coverage-aware football analytics beyond a single metric.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#analysis">
          Skip to analysis
        </a>
        {children}
      </body>
    </html>
  );
}
