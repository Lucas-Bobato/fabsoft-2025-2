import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { Theme } from '@radix-ui/themes';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'SlamTalk',
  description: 'A sua comunidade de basquete.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} text-white antialiased`}>
        <Theme accentColor="iris" grayColor="mauve" radius="large" scaling="90%">
          <AuthProvider>{children}</AuthProvider>
        </Theme>
      </body>
    </html>
  );
}