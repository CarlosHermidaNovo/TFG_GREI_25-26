"use client"

import { useState, useEffect } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { Chatbot } from "@/components/chatbot"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Globe, Info, Database, CheckCircle2 } from "lucide-react"

const PAISES = [
  { value: "España", flag: "🇪🇸", descripcion: "Datos desde 1990 hasta 2022" },
  { value: "Alemania", flag: "🇩🇪", descripcion: "Datos desde 1990 hasta 2022" },
  { value: "Italia", flag: "🇮🇹", descripcion: "Datos desde 1990 hasta 2022" },
]

const FUENTES = [
  {
    nombre: "FAO — Food and Agriculture Organization",
    descripcion: "Principal fuente de datos agrícolas, nutricionales y de seguridad alimentaria. Incluye métricas de producción de cereales, uso de fertilizantes, tierras arables y subalimentación.",
    url: "https://www.fao.org/faostat",
  },
  {
    nombre: "Datos propios — Predicción SARIMAX (Grecia)",
    descripcion: "Serie temporal de producción de trigo en Grecia enriquecida con variables exógenas propias: precios de urea, gas natural y electricidad. El modelo SARIMAX fue entrenado y validado mediante cortes históricos entre 2018 y 2023 usando causalidad de Granger para seleccionar variables.",
    url: null,
  },
]

export default function AjustesPage() {
  const [paisPredeterminado, setPaisPredeterminado] = useState("España")
  const [guardado, setGuardado] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem("sosfood_default_country")
    if (saved) setPaisPredeterminado(saved)
  }, [])

  function handlePaisChange(value: string) {
    setPaisPredeterminado(value)
    localStorage.setItem("sosfood_default_country", value)
    setGuardado(true)
    setTimeout(() => setGuardado(false), 2000)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />

      <main className="flex flex-1 flex-col overflow-y-auto">
        <header className="flex h-14 shrink-0 items-center border-b bg-card px-6 gap-2">
          <h1 className="text-sm font-semibold text-card-foreground">Ajustes</h1>
        </header>

        <div className="flex flex-col gap-6 p-6 max-w-2xl">

          {/* País predeterminado */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">País predeterminado</CardTitle>
              </div>
              <CardDescription>
                País que se muestra al abrir el Dashboard principal. Se guarda en este navegador.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={paisPredeterminado} onValueChange={handlePaisChange} className="flex flex-col gap-3">
                {PAISES.map((p) => (
                  <Label
                    key={p.value}
                    htmlFor={p.value}
                    className="flex items-center gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors hover:bg-secondary has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5"
                  >
                    <RadioGroupItem value={p.value} id={p.value} />
                    <span className="text-lg">{p.flag}</span>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{p.value}</span>
                      <span className="text-xs text-muted-foreground">{p.descripcion}</span>
                    </div>
                  </Label>
                ))}
              </RadioGroup>

              {guardado && (
                <div className="mt-3 flex items-center gap-1.5 text-xs text-primary">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Guardado
                </div>
              )}
            </CardContent>
          </Card>

          <Separator />

          {/* Acerca de */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">Acerca de SOS Food</CardTitle>
              </div>
              <CardDescription>
                Plataforma de análisis y visualización de datos de seguridad alimentaria y agricultura desarrollada como Trabajo de Fin de Grado.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 text-sm text-muted-foreground">
              <p>
                SOS Food permite explorar métricas clave de seguridad alimentaria en España, Alemania e Italia mediante un asistente conversacional, dashboards interactivos en Grafana y un modelo de predicción SARIMAX para la producción de trigo en Grecia.
              </p>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  { valor: "50+", label: "Métricas" },
                  { valor: "3", label: "Países" },
                  { valor: "30+", label: "Años de datos" },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-lg border bg-secondary/50 px-3 py-4">
                    <p className="text-xl font-bold text-card-foreground">{stat.valor}</p>
                    <p className="text-xs mt-0.5">{stat.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Fuentes de datos */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">Fuentes de datos</CardTitle>
              </div>
              <CardDescription>
                Organismos e instituciones de los que provienen los datos mostrados en la plataforma.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {FUENTES.map((f) => (
                <div key={f.nombre} className="rounded-lg border px-4 py-3 flex flex-col gap-1">
                  {f.url ? (
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-primary hover:underline"
                    >
                      {f.nombre}
                    </a>
                  ) : (
                    <span className="text-sm font-medium text-card-foreground">{f.nombre}</span>
                  )}
                  <p className="text-xs text-muted-foreground">{f.descripcion}</p>
                </div>
              ))}
            </CardContent>
          </Card>

        </div>
      </main>

      <Chatbot />
    </div>
  )
}
