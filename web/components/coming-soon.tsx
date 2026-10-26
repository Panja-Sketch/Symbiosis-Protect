import { Card, CardBody } from "@/components/ui/card";

/** Honest placeholder for screens whose build phase has not landed yet. No fake data is shown. */
export function ComingSoon({ title, phase, children }: { title: string; phase: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold md:text-3xl">{title}</h1>
      <Card>
        <CardBody className="space-y-2 pt-4 text-sm">
          <p className="inline-block rounded-full bg-surface-2 px-3 py-1 text-xs font-semibold uppercase">Arrives in {phase}</p>
          {children}
        </CardBody>
      </Card>
    </div>
  );
}
