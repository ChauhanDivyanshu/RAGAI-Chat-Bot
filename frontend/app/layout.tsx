import type { Metadata } from "next";
import { Inter, Cormorant_Garamond } from "next/font/google";  // ← Add this
import { Toaster } from "react-hot-toast";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
});

// ← Add this
const cormorant = Cormorant_Garamond({ 
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "RAG Assistant - AI Document Chat",
  description: "Production-grade RAG system with multilingual support",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      {/* ← Add cormorant.variable */}
      <body className={`${inter.variable} ${cormorant.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="mesh-bg min-h-screen">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              className: "glass",
              style: {
                background: "var(--card)",
                color: "var(--card-foreground)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
              },
              success: {
                iconTheme: {
                  primary: "#10b981",
                  secondary: "white",
                },
              },
              error: {
                iconTheme: {
                  primary: "#ef4444",
                  secondary: "white",
                },
              },
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  );
}