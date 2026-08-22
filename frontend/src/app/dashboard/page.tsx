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

  if (loading) return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-pulse flex space-x-2 items-center text-slate-500">
          <div className="w-4 h-4 bg-slate-400 rounded-full"></div>
          <span>Loading insights...</span>
        </div>
      </div>
    </div>
  );

  if (!data) return null;

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          
          <div className="flex justify-between items-end">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Operations Dashboard</h1>
              <p className="text-slate-500 mt-1">Proactive issue detection and SLA monitoring across all accounts.</p>
            </div>
            <div className="text-sm px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded-full font-medium flex items-center space-x-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              <span>Live Updates</span>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Open Tickets</p>
                  <h3 className="text-3xl font-bold text-slate-900 dark:text-white mt-1">{data.sla_stats.total_open}</h3>
                </div>
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </div>
            
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">SLA Breached</p>
                  <h3 className="text-3xl font-bold text-red-600 dark:text-red-400 mt-1">{data.sla_stats.breached}</h3>
                </div>
                <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">SLA At Risk (&lt;1h)</p>
                  <h3 className="text-3xl font-bold text-amber-600 dark:text-amber-400 mt-1">{data.sla_stats.at_risk}</h3>
                </div>
                <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                  <Clock className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Critical Alerts */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-red-500" />
                <span>Action Required</span>
              </h2>
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                {data.alerts.length === 0 ? (
                   <div className="p-6 text-center text-slate-500 flex flex-col items-center">
                     <ShieldCheck className="w-8 h-8 text-emerald-500 mb-2" />
                     <p>All good! No critical alerts.</p>
                   </div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {data.alerts.map((alert: any) => (
                      <div key={alert.id} className="p-4 flex items-start space-x-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                        <div className={`mt-1 flex-shrink-0 w-2 h-2 rounded-full ${
                          alert.severity === 'P1' ? 'bg-red-500' : 
                          alert.severity === 'WARNING' ? 'bg-amber-500' : 'bg-orange-400'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start">
                            <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                              {alert.message}
                            </p>
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                              {alert.ticket_id}
                            </span>
                          </div>
                          <div className="mt-1 flex items-center space-x-2 text-xs text-slate-500">
                            <span className="uppercase font-semibold">{alert.severity}</span>
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
              <h2 className="text-xl font-semibold flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                <span>Detected Patterns</span>
              </h2>
              <div className="space-y-4">
                {data.patterns.length === 0 ? (
                  <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 text-center text-slate-500">
                     No recurring patterns detected.
                  </div>
                ) : (
                  data.patterns.map((pattern: any, idx: number) => (
                    <div key={idx} className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-slate-900 dark:text-white">{pattern.title}</h3>
                        <span className="inline-flex items-center justify-center px-2 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                          {pattern.count} tickets
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{pattern.description}</p>
                      <div className="text-xs text-slate-500 flex flex-wrap gap-2">
                        {pattern.related_known_issue && (
                           <span className="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">Known Issue: {pattern.related_known_issue}</span>
                        )}
                        <span className="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">Affected: {pattern.affected_accounts.join(", ")}</span>
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
