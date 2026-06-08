"use client"

import { useState } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { GrafanaPanel } from "@/components/grafana-panel"
import { Chatbot } from "@/components/chatbot"

export default function DashboardPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left: Collapsible sidebar */}
      <AppSidebar />

      {/* Center: Dashboard content */}
      <main className="flex flex-1 flex-col overflow-y-auto">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center border-b bg-card px-6">
          <h1 className="text-sm font-semibold text-card-foreground">
            Dashboard
          </h1>
          <span className="ml-2 rounded-md bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
            En vivo
          </span>
        </header>

        {/* Dashboard body */}
        <div className="flex flex-1 flex-col gap-5 p-5">
          {/* Grafana Panel */}
          <GrafanaPanel />
        </div>
      </main>

      {/* Right: Collapsible chatbot */}
      <Chatbot />
    </div>
  )
}
