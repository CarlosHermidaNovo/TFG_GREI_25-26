"use client"

import React, { createContext, useContext, useState } from "react"
import { useRouter } from "next/navigation"

const BACKEND_URL = "http://localhost:8000"

export interface Message {
  id: string
  role: "user" | "bot"
  text: string
}

const INITIAL_MESSAGES: Message[] = [
  {
    id: "1",
    role: "bot",
    text: "Hola, soy el asistente de SOS Food. Puedo mostrarte datos sobre seguridad alimentaria, población rural, producción agrícola y más. Pregúntame lo que necesites.",
  },
]

interface ChatContextType {
  messages: Message[]
  input: string
  setInput: (value: string) => void
  isTyping: boolean
  grafanaUrls: string[]
  setGrafanaUrls: React.Dispatch<React.SetStateAction<string[]>>
  handleSend: () => Promise<void>
  chatOpen: boolean
  setChatOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [grafanaUrls, setGrafanaUrls] = useState<string[]>([])
  const [chatOpen, setChatOpen] = useState(true)

  async function handleSend() {
    const text = input.trim()
    if (!text || isTyping) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      text,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsTyping(true)

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: text }),
      })

      if (!res.ok) {
        throw new Error(`Error del servidor: ${res.status}`)
      }

      const data = await res.json()
      const respuesta: string = data.respuesta

      const urlMatch = respuesta.match(/(http:\/\/localhost:3000\/d\/[^\s]+)/)
      const routeMatch = respuesta.match(/ROUTE:\s*(\/\S*)/)

      let displayText = respuesta
      if (routeMatch) {
        const routeTo = routeMatch[1]
        router.push(routeTo)
        // Eliminamos silenciosamente solo la directiva técnica final
        displayText = respuesta.replace(/ROUTE:\s*\/[^\s]+/, "\n*(Navegando al panel automático...)*")
      } else if (urlMatch) {
        const urlToSet = urlMatch[1]
        setGrafanaUrls((prev) => [urlToSet, ...prev])
        displayText = respuesta.replace(urlMatch[0], "\n*(Gráfico enviado a las visualizaciones de usuario)*")
        router.push("/visualizaciones")
      }

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        text: displayText,
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        text: `Error al conectar con el servidor. Asegúrate de que el backend está corriendo en ${BACKEND_URL}.`,
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <ChatContext.Provider
      value={{
        messages,
        input,
        setInput,
        isTyping,
        grafanaUrls,
        setGrafanaUrls,
        handleSend,
        chatOpen,
        setChatOpen
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider")
  }
  return context
}
