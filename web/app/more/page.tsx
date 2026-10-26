import Link from "next/link";
import { Bell, ChevronRight, MapPin, Radio, Settings } from "lucide-react";

const LINKS = [
  { href: "/place", label: "My place", note: "Equipment ages and local history", icon: MapPin },
  { href: "/alerts", label: "Alerts", note: "Weather and task notifications", icon: Bell },
  { href: "/sense", label: "Sense", note: "Connect a water device", icon: Radio },
  { href: "/settings", label: "Settings", note: "Channels, quiet hours, sharing", icon: Settings },
];

export default function MorePage() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold">More</h1>
      <ul className="divide-y divide-line rounded-card border border-line bg-surface">
        {LINKS.map(({ href, label, note, icon: Icon }) => (
          <li key={href}>
            <Link href={href} className="flex min-h-[56px] items-center gap-3 px-4 py-2 hover:bg-surface-2">
              <Icon className="h-5 w-5 text-accent-text" aria-hidden />
              <span className="flex-1">
                <span className="block font-semibold">{label}</span>
                <span className="block text-sm text-muted">{note}</span>
              </span>
              <ChevronRight className="h-4 w-4 text-muted" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
