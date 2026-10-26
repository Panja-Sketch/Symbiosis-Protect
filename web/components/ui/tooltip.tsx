"use client";

import * as React from "react";
import * as T from "@radix-ui/react-tooltip";
import { cn } from "@/lib/utils";

export function Tip({ content, children, className }: { content: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <T.Provider delayDuration={150}>
      <T.Root>
        <T.Trigger asChild>{children}</T.Trigger>
        <T.Portal>
          <T.Content
            sideOffset={6}
            className={cn("z-[60] max-w-[260px] rounded-lg bg-ink px-3 py-2 text-xs text-bg shadow-lift", className)}
          >
            {content}
            <T.Arrow className="fill-ink" />
          </T.Content>
        </T.Portal>
      </T.Root>
    </T.Provider>
  );
}
