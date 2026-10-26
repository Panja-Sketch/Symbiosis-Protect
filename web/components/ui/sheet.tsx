"use client";

import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Sheet = Dialog.Root;
export const SheetTrigger = Dialog.Trigger;
export const SheetClose = Dialog.Close;

/** Bottom sheet on phones, right-side panel on laptops. */
export function SheetContent({
  className,
  children,
  title,
  description,
}: {
  className?: string;
  children: React.ReactNode;
  title: string;
  description?: string;
}) {
  return (
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40 animate-fade-in" />
      <Dialog.Content
        className={cn(
          "fixed z-50 flex flex-col bg-surface shadow-lift outline-none",
          "inset-x-0 bottom-0 max-h-[92dvh] rounded-t-2xl animate-slide-up",
          "md:inset-y-0 md:left-auto md:right-0 md:max-h-none md:w-[480px] md:rounded-none md:rounded-l-2xl",
          className,
        )}
      >
        <div className="flex items-start justify-between gap-3 border-b border-line p-4">
          <div>
            <Dialog.Title className="font-display text-xl font-semibold leading-tight">{title}</Dialog.Title>
            {description ? (
              <Dialog.Description className="mt-1 text-sm text-muted">{description}</Dialog.Description>
            ) : (
              <Dialog.Description className="sr-only">Details</Dialog.Description>
            )}
          </div>
          <Dialog.Close
            aria-label="Close"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg hover:bg-surface-2"
          >
            <X className="h-5 w-5" aria-hidden />
          </Dialog.Close>
        </div>
        <div className="flex-1 overflow-y-auto p-4">{children}</div>
      </Dialog.Content>
    </Dialog.Portal>
  );
}
