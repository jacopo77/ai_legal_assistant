import "./globals.css";
import GoogleAnalytics from "./GoogleAnalytics";

export const metadata = {
  title: "Legal Search Hub - Instant Legal Answers with Citations",
  description: "Get instant legal answers with citations to real laws. Free AI-powered legal research tool for everyone."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <GoogleAnalytics />
        {children}
      </body>
    </html>
  );
}
