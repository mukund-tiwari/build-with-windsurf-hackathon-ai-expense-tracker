"use client";
import { useState } from "react";

interface Message {
  role: "user" | "assistant" | "status";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;
    const textToSend = input;
    setMessages((prev) => [...prev, { role: "user", content: textToSend }, { role: "status", content: "Sending..." }]);
    setInput("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToSend }),
      });
      const data = await res.json();
      setMessages((prev) => {
        const withoutStatus = prev.filter((m) => m.role !== "status");
        let newMsgs: Message[] = [];
        if (data.action === "parse_expense" && data.expense) {
          const e = data.expense;
          newMsgs = [
            {
              role: "assistant",
              content: `Expense recorded: ₹${e.amount} on ${e.timestamp} for ${e.description}${
                e.category ? ` (category: ${e.category})` : ""
              }`,
            },
          ];
        } else if (data.action === "query_expenses" && data.expenses) {
          if (data.expenses.length === 0) {
            newMsgs = [{ role: "assistant", content: "No expenses found for that query." }];
          } else {
            const lines = data.expenses.map(
              (e: any) =>
                `- ₹${e.amount} on ${e.timestamp}: ${e.description}${
                  e.category ? ` (cat: ${e.category})` : ""
                }`
            );
            newMsgs = [{ role: "assistant", content: ["Expenses:", ...lines].join("\n") }];
          }
        } else if (data.action === "summarize_expenses" && data.summary) {
          const s = data.summary;
          const lines = ["Total: ₹" + s.total];
          if (s.breakdown && s.breakdown.length) {
            lines.push("Breakdown:");
            s.breakdown.forEach((b: any) => lines.push(`- ${b.period}: ₹${b.total}`));
          }
          newMsgs = [{ role: "assistant", content: lines.join("\n") }];
        } else if (data.action === "get_last_expense" && data.expense) {
          const e = data.expense;
          const parts = e.participants && e.participants.length ? ` (participants: ${e.participants.join(", ")})` : "";
          newMsgs = [
            {
              role: "assistant",
              content: `Last expense: ₹${e.amount} on ${e.timestamp} for ${e.description}${parts}`,
            },
          ];
        } else if (data.action === "split_expense" && data.split) {
          const s = data.split;
          newMsgs = [
            {
              role: "assistant",
              content: `Share for ${s.participant}: ₹${s.share.toFixed(2)}`,
            },
          ];
        } else if (data.response) {
          newMsgs = [{ role: "assistant", content: data.response }];
        } else {
          newMsgs = [{ role: "assistant", content: JSON.stringify(data) }];
        }
        return [...withoutStatus, ...newMsgs];
      });
    } catch (err: any) {
      setMessages((prev) => [
        ...prev.filter((m) => m.role !== "status"),
        { role: "assistant", content: "Error: " + err.message },
      ]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-4">
      {/* Header */}
      <header className="w-full max-w-md text-center mb-4">
        <h1 className="text-3xl font-extrabold text-black">AI Expense Tracker</h1>
        <p className="mt-2 text-black">
          Log expenses and get instant insights—all in natural language.
        </p>
      </header>
      {/* Chat Window */}
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-4 flex-1 flex flex-col">
        <div id="chat-container" className="flex-1 overflow-y-auto mb-4">
          {messages.map((m, i) => {
            // Determine container alignment and bubble styles
            let containerClasses = 'mb-2 flex ';
            let bubbleClasses = 'inline-block px-4 py-2 rounded-lg ';
            if (m.role === 'user') {
              containerClasses += 'justify-end';
              bubbleClasses += 'bg-blue-500 text-white';
            } else if (m.role === 'assistant') {
              containerClasses += 'justify-start';
              bubbleClasses += 'bg-gray-200 text-black';
            } else {
              containerClasses += 'justify-center';
              bubbleClasses += 'bg-gray-100 text-black italic';
            }
            return (
              <div key={i} className={containerClasses}>
                <span className={bubbleClasses}>{m.content}</span>
              </div>
            );
          })}
        </div>
        <div className="flex items-center">
          <textarea
            className="flex-1 border border-gray-300 rounded-md p-2 mr-2 focus:ring-2 focus:ring-blue-500 placeholder-black"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            rows={2}
            placeholder="Type expense or question and press Enter..."
          />
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
