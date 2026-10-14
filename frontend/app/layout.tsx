import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SawtOS | Carrier-Grade LiveKit Voice & Telephony Console',
  description: 'Enterprise Real-Time Voice AI, Telephony Orchestration & Conversational Analytics for US & Gulf Markets',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-emerald-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
