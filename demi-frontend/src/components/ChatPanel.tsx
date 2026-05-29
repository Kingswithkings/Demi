"use client";

import { useState } from "react";
import { sendMessageToDemi } from "@/lib/api";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatPanel() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello Kings. Tell me what you want to plan, organise, schedule, or execute.",
    },
  ]);

  const [loading, setLoading] = useState(false);

  async function handleSend() {
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: message,
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const data = await sendMessageToDemi(message);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content:
          data.reply ||
          data.response ||
          data.message ||
          "Demi received your request.",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I could not connect to the Demi backend. Check if FastAPI is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 min-h-[650px] flex flex-col">
      <h3 className="text-lg font-semibold mb-4">Chat with Demi</h3>

      <div className="flex-1 space-y-4 overflow-y-auto">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-4 rounded-xl max-w-xl ${
              msg.role === "user"
                ? "bg-emerald-500 text-slate-950 ml-auto"
                : "bg-slate-800 text-slate-300"
            }`}
          >
            <p className="text-sm">{msg.content}</p>
          </div>
        ))}

        {loading && (
          <div className="bg-slate-800 p-4 rounded-xl max-w-xl text-sm text-slate-400">
            Demi is thinking...
          </div>
        )}
      </div>

      <div className="mt-6 flex gap-3">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          placeholder="Ask Demi to schedule, plan, organise, or execute..."
          className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-emerald-500"
        />

        <button
          onClick={handleSend}
          disabled={loading}
          className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold px-6 rounded-xl"
        >
          Send
        </button>
      </div>
    </section>
  );
}
