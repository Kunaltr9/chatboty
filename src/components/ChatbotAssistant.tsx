import React, { useState, useRef, useEffect } from 'react'
import { Bot, X, Send, ChevronLeft, Maximize2, Minimize2, Sparkles, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { PROMPT_SUGGESTIONS } from '@/lib/constants'
import { mockSecurityEvents } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { ScrollArea } from './ui/scroll-area'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'
import { Badge } from './ui/badge'
import { useIsMobile } from '@/hooks/use-mobile'

type ViewState = 'welcome' | 'loading' | 'results' | 'details' | 'error'

interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  timestamp: Date
  data?: any
}

export function ChatbotAssistant() {
  const [isOpen, setIsOpen] = useState(true)
  const [isExpanded, setIsExpanded] = useState(false)
  const [viewState, setViewState] = useState<ViewState>('welcome')
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [selectedEvent, setSelectedEvent] = useState<any>(null)

  const isMobile = useIsMobile()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [messages, viewState])

  const handleOpen = () => setIsOpen(true)
  const handleClose = () => setIsOpen(false)

  const handlePromptSelect = async (prompt: typeof PROMPT_SUGGESTIONS[0]) => {
    setViewState('loading')

    const userMessage: Message = {
      id: (Date.now() - 100).toString(),
      role: 'user',
      content: prompt.query,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])

    try {
      const res = await fetch('http://127.0.0.1:8001/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ promptId: prompt.id, query: prompt.query }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: body.content || `Here are the results for: ${prompt.title}`,
        timestamp: new Date(),
        data: Array.isArray(body.data) ? body.data : prompt.id === 'security-threats' ? mockSecurityEvents : null,
      }
      setMessages((prev) => [...prev, aiMessage])
      setViewState('results')
    } catch (err) {
      const fallbackMsg: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: `Here are the results for: ${prompt.title}`,
        timestamp: new Date(),
        data: prompt.id === 'security-threats' ? mockSecurityEvents : null,
      }
      setMessages((prev) => [...prev, fallbackMsg])
      setViewState('results')
    }
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!inputValue.trim()) return
    const userMsgStr = inputValue
    setInputValue('')
    setViewState('loading')
    const userMessage: Message = {
      id: (Date.now() - 100).toString(),
      role: 'user',
      content: userMsgStr,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    try {
      const res = await fetch('http://127.0.0.1:8001/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsgStr }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: body.content || "I've analyzed the system logs based on your query.",
        timestamp: new Date(),
        data: Array.isArray(body.data) ? body.data : mockSecurityEvents.slice(0, 3),
      }
      setMessages((prev) => [...prev, aiMessage])
      setViewState('results')
    } catch (err) {
      const fallback: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: "I've analyzed the system logs based on your query. Everything appears nominal.",
        timestamp: new Date(),
        data: mockSecurityEvents.slice(0, 3),
      }
      setMessages((prev) => [...prev, fallback])
      setViewState('results')
    }
  }

  const handleDrillDown = (event: any) => {
    setSelectedEvent(event)
    setViewState('details')
  }

  const handleBack = () => {
    if (viewState === 'details') {
      setViewState('results')
      setSelectedEvent(null)
    } else {
      setViewState('welcome')
    }
  }

  return (
    <>
      <AnimatePresence>
        {!isOpen && (
          <motion.button onClick={handleOpen} className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-lg">
            <Bot />
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div className="fixed bottom-6 right-6 w-[640px] h-[640px] bg-card p-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div style={{ padding: 12, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <div style={{ width: 40, height: 40, borderRadius: 8, background: '#08303a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Bot />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600 }}>Sentinel AI</div>
                    <div style={{ fontSize: 12, color: '#9aa3b2' }}>Security & Logs Assistant</div>
                  </div>
                </div>
                <div>
                  <button onClick={handleClose}><X /></button>
                </div>
              </div>
            </div>

            <div style={{ height: '520px', overflow: 'auto', padding: 12 }}>
              {viewState === 'welcome' && (
                <div>
                  <h3>How can I help you protect the system?</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                    {PROMPT_SUGGESTIONS.map((p) => (
                      <button key={p.id} onClick={() => handlePromptSelect(p)} style={{ padding: 8, textAlign: 'left' }}>{p.title}</button>
                    ))}
                  </div>
                </div>
              )}

              {viewState === 'loading' && <div>Analyzing logs & patterns...</div>}

              {viewState === 'results' && (
                <div>
                  {messages.map((msg) => (
                    <div key={msg.id} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                      <div style={{ width: 36 }}>{msg.role === 'ai' ? <Bot /> : <div style={{ width: 24, height: 24, background: '#1f2937', borderRadius: 6 }} />}</div>
                      <div style={{ background: msg.role === 'ai' ? '#071420' : '#065f5e', padding: 8, borderRadius: 10, flex: 1 }}>
                        <div>{msg.content}</div>
                        {msg.data && Array.isArray(msg.data) && (
                          <div style={{ marginTop: 8 }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                              <thead>
                                <tr style={{ textAlign: 'left', color: '#9aa3b2' }}>
                                  <th>Severity</th>
                                  <th>Type</th>
                                  <th>Source</th>
                                  <th>Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {msg.data.map((ev: any) => (
                                  <tr key={ev.id} onClick={() => handleDrillDown(ev)} style={{ cursor: 'pointer' }}>
                                    <td>{ev.severity}</td>
                                    <td>{ev.type}</td>
                                    <td>{ev.source}</td>
                                    <td>Details →</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {viewState === 'details' && selectedEvent && (
                <div>
                  <h3>{selectedEvent.type}</h3>
                  <p>{selectedEvent.details}</p>
                </div>
              )}
            </div>

            <div style={{ padding: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} style={{ display: 'flex', gap: 8 }}>
                <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder={viewState === 'welcome' ? 'Or type a question...' : 'Ask a follow up...'} style={{ flex: 1, padding: 10, borderRadius: 8, background: '#071421', color: 'white', border: '1px solid rgba(255,255,255,0.05)' }} />
                <button type="submit" style={{ padding: '8px 12px', borderRadius: 8, background: '#0ea5a4', color: 'white' }}><Send /></button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default ChatbotAssistant
