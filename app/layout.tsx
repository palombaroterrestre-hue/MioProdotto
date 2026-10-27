import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MioProdotto - Versione di prova',
  description: 'Riconosci i prodotti dalla foto e seguili nella tua lista. Offerte storiche, non prezzi attuali.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  )
}
