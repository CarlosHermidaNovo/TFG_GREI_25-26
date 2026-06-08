"use client"

import { Sprout } from "lucide-react"

interface DynamicVisualizationProps {
  grafanaUrl: string | null
}

export function DynamicVisualization({ grafanaUrl }: DynamicVisualizationProps) {
  if (!grafanaUrl) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-xl border bg-card p-8 shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
          <Sprout className="h-8 w-8 text-primary" />
        </div>
        <h3 className="mt-5 text-balance text-center text-lg font-semibold text-card-foreground">
          Pídeme cualquier dato sobre seguridad alimentaria
        </h3>
        <p className="mt-2 max-w-sm text-center text-sm leading-relaxed text-muted-foreground">
          Escribe una pregunta en el chat y generaré una visualización
          interactiva con los datos relevantes en este panel.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {[
            "Muéstrame el PIB",
            "Evolución de la obesidad",
            "Población rural",
            "Producción de cereales",
          ].map((tag) => (
            <span
              key={tag}
              className="rounded-full border bg-secondary px-3 py-1 text-xs font-medium text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col rounded-xl border bg-card shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 border-b px-5 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Sprout className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">
            Visualización solicitada
          </h3>
          <p className="text-[11px] text-muted-foreground">
            Generada por el asistente
          </p>
        </div>
      </div>

      {/* Grafana iframe */}
      <div className="flex-1 overflow-hidden">
        <iframe
          src={grafanaUrl}
          title="Visualización Grafana"
          width="100%"
          height="100%"
          frameBorder="0"
          allow="fullscreen"
        />
      </div>
    </div>
  )
}
