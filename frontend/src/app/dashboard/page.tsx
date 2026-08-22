"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AlertCircle, Clock, ShieldAlert, TrendingUp, ShieldCheck } from "lucide-react";
import Sidebar from "@/components/Sidebar";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getDashboardInsights();
        setData(result);
      } catch (e) {
        // Silently handle retry without triggering Next.js dev overlay
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen bg-white text-black">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex space-x-2 items-center text-black font-mono text-sm border-2 border-black p-4">
            <span className="w-3 h-3 bg-black animate-ping" />
            <span>Auditing operational tickets & computing SLA analytics...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-screen bg-white text-black">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="border-2 border-black p-6 max-w-md text-center space-y-3">
            <h3 className="font-bold text-lg">Connecting to Insights API...</h3>
            <p className="text-sm text-gray-600">Fetching live operational metrics from backend.</p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-black text-white px-4 py-2 text-sm font-mono hover:bg-gray-800"
            >
              Refresh Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white text-black overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          
          <div className="flex justify-between items-end border-b-2 border-black pb-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-black">Operations Dashboard</h1>
              <p className="text-gray-600 mt-1 font-mono text-sm">Proactive issue detection and SLA monitoring across all accounts.</p>
            </div>
            <div className="text-xs px-3 py-1 bg-black text-white font-mono font-bold flex items-center space-x-2">
              <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span>LIVE SLA AUDIT</span>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 border-2 border-black">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-xs font-mono uppercase font-bold text-gray-600">Open Tickets</p>
                  <h3 className="text-4xl font-bold text-black mt-2">{data.sla_stats.total_open}</h3>
                </div>
                <div className="p-2 border-2 border-black">
                  <Activity className="w-6 h-6 text-black" />
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 border-2 border-black">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-xs font-mono uppercase font-bold text-gray-600">SLA Breached</p>
                  <h3 className="text-4xl font-bold text-black mt-2 underline decoration-2">{data.sla_stats.breached}</h3>
                </div>
                <div className="p-2 bg-black text-white">
                  <AlertCircle className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 border-2 border-black">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-xs font-mono uppercase font-bold text-gray-600">SLA At Risk (&lt;1h)</p>
                  <h3 className="text-4xl font-bold text-black mt-2">{data.sla_stats.at_risk}</h3>
                </div>
                <div className="p-2 border border-black">
                  <Clock className="w-6 h-6 text-black" />
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Critical Alerts */}
            <div className="space-y-4">
              <h2 className="text-lg font-bold uppercase tracking-wider flex items-center space-x-2 border-b-2 border-black pb-2">
                <ShieldAlert className="w-5 h-5 text-black" />
                <span>Critical SLA Alerts</span>
              </h2>
              <div className="bg-white border-2 border-black overflow-hidden">
                {data.alerts.length === 0 ? (
                   <div className="p-6 text-center text-gray-500 flex flex-col items-center">
                     <ShieldCheck className="w-8 h-8 text-black mb-2" />
                     <p className="font-mono text-xs">All SLAs are currently within targets.</p>
                   </div>
                ) : (
                  <div className="divide-y-2 divide-black">
                    {data.alerts.map((alert: any) => (
                      <div key={alert.id} className="p-4 flex items-start space-x-4 hover:bg-gray-50 transition-colors">
                        <div className="mt-1 flex-shrink-0 w-2.5 h-2.5 bg-black" />
                        <div className="flex-1 min-w-0 font-mono text-xs">
                          <div className="flex justify-between items-start">
                            <p className="font-bold text-black truncate">
                              {alert.message}
                            </p>
                            <span className="ml-2 px-1.5 py-0.5 border border-black font-bold">
                              {alert.ticket_id}
                            </span>
                          </div>
                          <div className="mt-2 flex items-center space-x-2 text-[11px] text-gray-600">
                            <span className="bg-black text-white px-1 font-bold">{alert.severity}</span>
                            <span>&bull;</span>
                            <span>{alert.account_id}</span>
                            <span>&bull;</span>
                            <span className="capitalize">{alert.type.replace("_", " ")}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Detected Patterns */}
            <div className="space-y-4">
              <h2 className="text-lg font-bold uppercase tracking-wider flex items-center space-x-2 border-b-2 border-black pb-2">
                <TrendingUp className="w-5 h-5 text-black" />
                <span>Detected Incident Patterns</span>
              </h2>
              <div className="space-y-4">
                {data.patterns.length === 0 ? (
                  <div className="bg-white border-2 border-black p-6 text-center text-gray-500 font-mono text-xs">
                     No recurring patterns detected.
                  </div>
                ) : (
                  data.patterns.map((pattern: any, idx: number) => (
                    <div key={idx} className="bg-white p-5 border-2 border-black space-y-2 font-mono">
                      <div className="flex justify-between items-start">
                        <h3 className="font-bold text-sm text-black">{pattern.title}</h3>
                        <span className="bg-black text-white px-2 py-0.5 text-xs font-bold">
                          {pattern.count} TICKETS
                        </span>
                      </div>
                      <p className="text-xs text-gray-700">{pattern.description}</p>
                      <div className="text-[11px] text-gray-600 flex flex-wrap gap-2 pt-1 border-t border-gray-200">
                        {pattern.related_known_issue && (
                           <span className="border border-black px-1.5 py-0.5">Issue: {pattern.related_known_issue}</span>
                        )}
                        <span className="border border-gray-400 px-1.5 py-0.5">Affected: {pattern.affected_accounts.join(", ")}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
          </div>
        </div>
      </main>
    </div>
  );
}

function Activity(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  )
}
