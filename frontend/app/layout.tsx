'use client';
import { useEffect } from 'react';
import WebApp from '@twa-dev/sdk';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
  }, []);

  return (
    <html lang="en">
      <body className="min-h-screen bg-[#12052A] text-white">{children}</body>
    </html>
  );
}