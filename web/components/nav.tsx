"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, FileText, Home, ListChecks, MapPin, Menu, MessageCircle, Radio, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/coverage", label: "Coverage", icon: FileText },
  { href: "/ask", label: "Ask", icon: MessageCircle },
  { href: "/place", label: "My place", icon: MapPin },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/sense", label: "Sense", icon: Radio },
  { href: "/settings", label: "Settings", icon: Settings },
];
const TABS = [...ITEMS.slice(0, 4), { href: "/more", label: "More", icon: Menu }];

function active(path: string, href: string) {
  return href === "/" ? path === "/" : path === href || path.startsWith(href + "/");
}

export function Sidebar({ unread }: { unread: number }) {
  const path = usePathname();
  return (
    <nav aria-label="Primary" className="hidden w-56 shrink-0 flex-col gap-1 border-r border-line bg-surface p-3 lg:flex">
      {ITEMS.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          aria-current={active(path, href) ? "page" : undefined}
          className={cn(
            "flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-sm font-medium hover:bg-surface-2",
            active(path, href) && "bg-accent-soft text-accent-text",
          )}
        >
          <Icon className="h-5 w-5" aria-hidden />
          {label}
          {href === "/alerts" && unread > 0 && (
            <span className="ml-auto rounded-full bg-clay-text px-2 py-0.5 text-xs font-semibold text-white dark:text-[#2a1008]">
              {unread}
              <span className="sr-only"> unread</span>
            </span>
          )}
        </Link>
      ))}
    </nav>
  );
}

export function TabBar({ unread }: { unread: number }) {
  const path = usePathname();
  const moreActive = ["/more", "/place", "/alerts", "/sense", "/settings"].some((p) => active(path, p));
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden"
    >
      {TABS.map(({ href, label, icon: Icon }) => {
        const on = href === "/more" ? moreActive : active(path, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={on ? "page" : undefined}
            className={cn(
              "relative flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-[11px] font-medium",
              on ? "text-accent-text" : "text-muted",
            )}
          >
            <Icon className="h-5 w-5" aria-hidden />
            {label}
            {href === "/more" && unread > 0 && (
              <span className="absolute right-[26%] top-1.5 h-2.5 w-2.5 rounded-full bg-clay-text" aria-label={`${unread} unread alerts`} />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
