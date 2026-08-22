import ChatWindow from "@/components/ChatWindow";

export default function InternalPage() {
  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-4 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold">Internal Operations Agent</h1>
          <p className="text-slate-500">Investigate customer issues, check SLAs, and resolve conflicts across all accounts.</p>
        </div>
        <div className="text-sm px-3 py-1 bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-full font-medium">
          Global Access Enabled
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <ChatWindow context="internal" />
      </div>
    </div>
  );
}
