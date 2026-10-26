"use client";

import { useEffect, useState } from "react";
import { Camera, CheckCircle2, FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Task } from "@/lib/types";

const LEVELS: Record<string, { label: string }> = {
  E0: { label: "One tap" },
  E1: { label: "Photo" },
  E2: { label: "Document" },
};

function getPosition(): Promise<{ lat: number; lon: number } | null> {
  if (typeof navigator === "undefined" || !navigator.geolocation) return Promise.resolve(null);
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => resolve(null),
      { timeout: 5000, maximumAge: 60000 },
    );
  });
}

/** E0 one-tap, E1 photo (camera on phones) with time + optional device location, E2 document. SHA-256 is computed by the server. */
export function ProofCapture({ task, onSubmitted }: { task: Task; onSubmitted: () => void }) {
  const options = task.proof_accepted.filter((l) => l in LEVELS);
  const [level, setLevel] = useState(options.includes(task.proof_default_level) ? task.proof_default_level : options[0]);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [geo, setGeo] = useState("Location is requested only when you submit a photo; you can decline.");

  useEffect(() => {
    if (!file || !file.type.startsWith("image/")) {
      setPreview(null);
      return;
    }
    const u = URL.createObjectURL(file);
    setPreview(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);

  async function submit() {
    setErr(null);
    setBusy(true);
    const fd = new FormData();
    fd.set("level", level);
    if (level !== "E0") {
      if (!file) {
        setBusy(false);
        setErr(level === "E1" ? "Take or choose a photo first." : "Choose a file first.");
        return;
      }
      fd.set("file", file);
      fd.set("client_captured_at", new Date(file.lastModified || Date.now()).toISOString());
      if (level === "E1") {
        const pos = await getPosition();
        if (pos) {
          fd.set("lat", String(pos.lat));
          fd.set("lon", String(pos.lon));
          setGeo("Location attached from your device.");
        } else {
          setGeo("Location not shared; the photo is recorded without it.");
        }
      }
    }
    const r = await fetch(`/backend/api/v1/tasks/${task.id}/complete`, { method: "POST", body: fd });
    setBusy(false);
    if (!r.ok) {
      setErr((await r.json().catch(() => ({}))).detail ?? "Upload failed");
      return;
    }
    onSubmitted();
  }

  return (
    <div className="mt-2 space-y-3" data-testid="proof-capture">
      <fieldset>
        <legend className="text-sm text-muted">How do you want to show it is done?</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {options.map((l) => (
            <label
              key={l}
              className={cn(
                "flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 text-sm font-medium focus-within:outline focus-within:outline-2 focus-within:outline-accent-strong",
                level === l ? "border-accent-strong bg-accent-soft text-accent-text" : "border-line",
              )}
            >
              <input
                type="radio"
                name={`proof-${task.id}`}
                value={l}
                checked={level === l}
                onChange={() => {
                  setLevel(l);
                  setFile(null);
                }}
                className="sr-only"
              />
              {l === "E1" ? <Camera className="h-4 w-4" aria-hidden /> : l === "E2" ? <FileUp className="h-4 w-4" aria-hidden /> : <CheckCircle2 className="h-4 w-4" aria-hidden />}
              {LEVELS[l].label} <span className="text-xs text-muted">({l})</span>
            </label>
          ))}
        </div>
      </fieldset>
      {level !== "E0" && (
        <div>
          <label className="block text-sm font-medium" htmlFor={`file-${task.id}`}>
            {level === "E1" ? "Take a photo" : "Choose a document or photo"}
          </label>
          <input
            id={`file-${task.id}`}
            data-testid="proof-file"
            type="file"
            accept={level === "E1" ? "image/*" : "image/*,application/pdf"}
            {...(level === "E1" ? { capture: "environment" as const } : {})}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block min-h-[44px] w-full rounded-lg border border-line bg-surface p-2 text-sm"
          />
          {preview && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Preview of your proof photo" className="mt-2 max-h-40 rounded-lg border border-line" />
          )}
          {level === "E1" && <p className="mt-1 text-xs text-muted">{geo}</p>}
        </div>
      )}
      {err && (
        <p role="alert" className="rounded-lg bg-clay-soft p-2 text-sm text-clay-text">
          {err}
        </p>
      )}
      <Button disabled={busy} onClick={submit} className="w-full" data-testid="proof-submit">
        <CheckCircle2 className="h-4 w-4" aria-hidden /> {level === "E0" ? "I did this" : "Submit proof and mark done"}
      </Button>
    </div>
  );
}
