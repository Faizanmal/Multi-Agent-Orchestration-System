import './globals.css';
import type { Metadata } from 'next';
import { QueryProvider } from '@/providers/QueryProvider';
import { AuthProvider } from '@/contexts/AuthContext';
import Script from 'next/script';

export const metadata: Metadata = {
  title: {
    template: '%s | Multi-Agent Orchestration',
    default: 'Multi-Agent Orchestration | The Future of AI Workflows',
  },
  description: 'Intelligent agent orchestration with real-time performance. Automate your workflows with multi-modal AI agents powered by Groq.',
  keywords: ['AI', 'Agents', 'Groq', 'Orchestration', 'Workflows', 'Automation', 'Premium AI', 'Multi-Agent System'],
  openGraph: {
    title: 'Multi-Agent Orchestration | The Future of AI Workflows',
    description: 'Intelligent agent orchestration with real-time performance.',
    type: 'website',
    url: 'https://multiagent.example.com',
    siteName: 'Multi-Agent Orchestration',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Multi-Agent Orchestration | The Future of AI Workflows',
    description: 'Intelligent agent orchestration with real-time performance.',
  },
  robots: {
    index: true,
    follow: true,
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const plausibleDomain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;

  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <QueryProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </QueryProvider>
        {plausibleDomain && (
          <Script 
            defer 
            data-domain={plausibleDomain} 
            src="https://plausible.io/js/script.js" 
            strategy="afterInteractive"
          />
        )}
      </body>
    </html>
  );
}
