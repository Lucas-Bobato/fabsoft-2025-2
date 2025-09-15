import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'SlamTalk',
  description: 'A sua comunidade de basquete.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} text-white antialiased`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}