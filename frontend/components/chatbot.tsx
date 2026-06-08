"use client"

import { useRef, useEffect, Fragment } from "react"
import { Send, Bot, User, MessageSquare, X, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useChat } from "@/context/chat-context"

function renderMarkdown(text: string) {
  return text.split("\n").map((line, i, arr) => {
    // Split by **bold** tokens
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    const rendered = parts.map((part, j) =>
      part.startsWith("**") && part.endsWith("**")
        ? <strong key={j}>{part.slice(2, -2)}</strong>
        : <Fragment key={j}>{part}</Fragment>
    )
    return (
      <Fragment key={i}>
        {rendered}
        {i < arr.length - 1 && <br />}
      </Fragment>
    )
  })
}

export function Chatbot() {
  const { messages, input, setInput, isTyping, handleSend, chatOpen, setChatOpen } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  return (
    <>
      {/* Collapsed state: floating toggle button */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105"
          aria-label="Abrir asistente"
        >
          <MessageSquare className="h-5 w-5" />
        </button>
      )}

      {/* Open panel */}
      <aside
        className={cn(
          "flex h-full flex-col border-l bg-card transition-all duration-300",
          chatOpen ? "w-[380px] opacity-100" : "w-0 overflow-hidden opacity-0"
        )}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center gap-2 border-b px-4 py-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Bot className="h-4 w-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-card-foreground">
              Asistente SOS Food
            </p>
            <p className="text-[11px] text-muted-foreground">
              Pregunta sobre datos alimentarios
            </p>
          </div>
          <button
            onClick={() => setChatOpen(false)}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-card-foreground"
            aria-label="Cerrar asistente"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-col gap-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-2",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground"
                  )}
                >
                  {msg.role === "user" ? (
                    <User className="h-3.5 w-3.5" />
                  ) : (
                    <Bot className="h-3.5 w-3.5" />
                  )}
                </div>
                <div
                  className={cn(
                    "max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-card-foreground"
                  )}
                >
                  {msg.role === "bot" ? renderMarkdown(msg.text) : msg.text}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-2">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary text-muted-foreground">
                  <Bot className="h-3.5 w-3.5" />
                </div>
                <div className="rounded-xl bg-secondary px-3.5 py-2.5">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="shrink-0 border-t p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe tu pregunta..."
              disabled={isTyping}
              className="flex-1 rounded-lg border bg-background px-3 py-2 text-sm outline-none ring-ring transition-shadow placeholder:text-muted-foreground focus:ring-2 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-opacity disabled:opacity-40"
              aria-label="Enviar mensaje"
            >
              {isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </form>
        </div>
      </aside>
    </>
  )
}
