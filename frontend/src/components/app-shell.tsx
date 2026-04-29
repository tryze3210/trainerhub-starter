'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = ['/', '/catalog', '/trainers', '/login', '/register', '/cabinet', '/orders', '/payments', '/subscriptions', '/entitlements'];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="shell">
      <header className="header">
        <div className="wrap">
          <Link href="/" className="brand">TrainerHub Frontend</Link>
          <nav className="nav">
            {links.map((href) => (
              <Link key={href} href={href} style={pathname===href?{outline:'1px solid #93c5fd'}:undefined}>{href==='/'?'home':href.slice(1)}</Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
