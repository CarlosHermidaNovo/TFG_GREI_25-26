"use client"

import { useState } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { Chatbot } from "@/components/chatbot"
import { BarChart3 } from "lucide-react"

export function GrafanaPanelTrigo() {
    return (
        <section className="flex flex-1 flex-col rounded-xl border bg-card shadow-sm">
            <div className="flex shrink-0 items-center gap-2 border-b px-5 py-3">
                <BarChart3 className="h-4 w-4 text-accent" />
                <h2 className="text-sm font-semibold text-card-foreground">
                    Predicción Trigo en Grecia (SARIMAX)
                </h2>
                <span className="ml-auto rounded-md bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                    En vivo
                </span>
            </div>

            <div className="relative flex-1 w-full overflow-hidden rounded-b-xl min-h-[500px]">
                <iframe
                    src="http://localhost:3000/d/adk6tw4/prediccion-trigo-grecia?orgId=1&kiosk"
                    title="Grafana Dashboard Trigo"
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

export default function TrigoPage() {
    return (
        <div className="flex h-screen overflow-hidden">
            <AppSidebar />
            <main className="flex flex-1 flex-col overflow-y-auto">
                <header className="flex h-14 shrink-0 items-center border-b bg-card px-6">
                    <h1 className="text-sm font-semibold text-card-foreground">Trigo en Grecia</h1>
                </header>

                <div className="flex flex-1 flex-col gap-5 p-5">
                    <GrafanaPanelTrigo />
                </div>
            </main>

            <Chatbot />
        </div>
    )
}
