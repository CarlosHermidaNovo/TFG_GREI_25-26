"use client"

import { useState, useEffect } from "react"
import { BarChart3 } from "lucide-react"
import { useSearchParams } from "next/navigation"

const BASE_URL = "http://localhost:3000/d/adgmg5p/visor-datos?orgId=1&kiosk"

export function GrafanaPanel() {
  const searchParams = useSearchParams()
  const paises = searchParams.getAll("pais")
  const [defaultCountry, setDefaultCountry] = useState("España")

  useEffect(() => {
    const saved = localStorage.getItem("sosfood_default_country")
    if (saved) setDefaultCountry(saved)
  }, [])

  let finalUrl = BASE_URL
  if (paises.length === 0) {
    finalUrl += `&var-pais=${encodeURIComponent(defaultCountry)}`
  } else {
    paises.forEach(pais => {
      finalUrl += `&var-pais=${encodeURIComponent(pais)}`
    })
  }
  return (
    <section className="flex flex-1 flex-col rounded-xl border bg-card shadow-sm">
      <div className="flex shrink-0 items-center gap-2 border-b px-5 py-3">
        <BarChart3 className="h-4 w-4 text-accent" />
        <h2 className="text-sm font-semibold text-card-foreground">
          Dashboard Grafana
        </h2>
        <span className="ml-auto rounded-md bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          En vivo
        </span>
      </div>

      <div className="relative flex-1 w-full overflow-hidden rounded-b-xl min-h-[500px]">
        <iframe
          src={finalUrl}
          title="Grafana Dashboard"
          width="100%"
          height="100%"
          frameBorder="0"
          className="rounded-b-xl"
          allow="fullscreen"
        />
      </div>
    </section>
  )
}
