"use client"

import { AppSidebar } from "@/components/app-sidebar"
import { Chatbot } from "@/components/chatbot"
import { DynamicVisualization } from "@/components/dynamic-visualization"
import { useChat } from "@/context/chat-context"

export default function VisualizacionesPage() {
    const { grafanaUrls } = useChat()

    return (
        <div className="flex h-screen overflow-hidden">
            <AppSidebar />
            <main className="flex flex-1 flex-col overflow-y-auto bg-background">
                <header className="flex h-14 shrink-0 items-center border-b bg-card px-6 sticky top-0 z-10">
                    <h1 className="text-sm font-semibold text-card-foreground">
                        Visualizaciones de usuario
                    </h1>
                </header>

                <div className="flex flex-col gap-8 p-6 pb-12">
                    {grafanaUrls.length === 0 ? (
                        <div className="min-h-[500px] flex flex-col">
                            <DynamicVisualization grafanaUrl={null} />
                        </div>
                    ) : (
                        grafanaUrls.map((url, index) => (
                            <div key={index} className="h-[500px] lg:h-[600px] shrink-0 flex flex-col">
                                <DynamicVisualization grafanaUrl={url} />
                            </div>
                        ))
                    )}
                </div>
            </main>
            <Chatbot />
        </div>
    )
}
