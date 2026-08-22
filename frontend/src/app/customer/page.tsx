import ChatWindow from "@/components/ChatWindow";

export default function CustomerPage() {
  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Support Chat</h1>
        <p className="text-slate-500">Ask questions about your account, orders, or policies.</p>
      </div>
      <div className="flex-1 min-h-0">
        <ChatWindow context="customer" />
      </div>
    </div>
  );
}
