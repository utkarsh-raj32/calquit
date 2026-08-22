"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, Check, X, Loader2 } from "lucide-react";
import { api, auth, type PendingAction } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ActionQueue() {
  const [actions, setActions] = useState<PendingAction[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchActions = async () => {
    // Only fetch if user is authenticated
    const token = auth.getToken();
    if (!token) return;
    
    try {
      const data = await api.getPendingActions();
      setActions(data.filter((a) => a.status === "pending_confirmation"));
    } catch (e) {
      // Silently ignore - backend may be down or user not authenticated
    }
  };

  useEffect(() => {
    fetchActions();
    const interval = setInterval(fetchActions, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (id: string, approve: boolean) => {
    setLoading(true);
    try {
      if (approve) {
        await api.confirmAction(id);
      } else {
        await api.rejectAction(id);
      }
      await fetchActions();
    } catch (e) {
      alert("Failed to process action");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (actions.length === 0) return null;

  return (
    <div className="absolute top-4 right-4 z-50 w-80 space-y-3">
      {actions.map((action) => (
        <div 
          key={action.action_id}
          className="bg-white border-2 border-black rounded-none shadow-none overflow-hidden animate-in slide-in-from-right"
        >
          <div className="bg-black p-3 border-b-2 border-black flex items-center space-x-2 text-white">
            <AlertTriangle className="w-4 h-4 text-white" />
            <h4 className="text-sm font-semibold text-white">Action Required</h4>
          </div>
          <div className="p-4 space-y-3">
            <div className="text-sm text-gray-800">
              <span className="font-bold text-black capitalize">
                {action.action_type.replace("_", " ")}
              </span> requested.
            </div>
            
            <div className="text-xs bg-white p-2 rounded-none border border-black font-mono overflow-auto max-h-32 text-black">
               {JSON.stringify(
                  Object.fromEntries(Object.entries(action).filter(([k]) => !['action_id', 'status', 'action_type', 'created_at'].includes(k))),
                  null,
                  2
               )}
            </div>
            
            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => handleAction(action.action_id, false)}
                disabled={loading}
                className="flex-1 flex items-center justify-center space-x-1 py-1.5 px-3 rounded-none text-sm text-black border border-black hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4" />
                <span>Reject</span>
              </button>
              <button
                onClick={() => handleAction(action.action_id, true)}
                disabled={loading}
                className="flex-1 flex items-center justify-center space-x-1 py-1.5 px-3 rounded-none text-sm text-white bg-black hover:bg-gray-800 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                <span>Confirm</span>
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
