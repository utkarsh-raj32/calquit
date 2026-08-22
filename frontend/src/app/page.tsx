"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Package, User as UserIcon, ShieldAlert, Loader2 } from "lucide-react";
import { api, auth } from "@/lib/api";

type MockUser = {
  username: string;
  name: string;
  role: string;
  account_id?: string;
};

export default function LandingPage() {
  const router = useRouter();
  const [users, setUsers] = useState<MockUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState<string | null>(null);

  useEffect(() => {
    // If already logged in, redirect
    const user = auth.getUser();
    if (user) {
      router.push(user.role === "customer" ? "/customer" : "/internal");
      return;
    }

    // Fetch mock users
    auth.getMockUsers()
      .then(setUsers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogin = async (username: string) => {
    setLoginLoading(username);
    try {
      const user = await auth.login(username);
      if (user) {
        router.push(user.role === "customer" ? "/customer" : "/internal");
      }
    } catch (e) {
      alert("Login failed. Ensure backend is running.");
      setLoginLoading(null);
    }
  };

  const customers = users.filter((u) => u.role === "customer");
  const internal = users.filter((u) => u.role !== "customer");

  if (loading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-black" /></div>;
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-8">
        
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-3 text-black">
            <Package className="w-12 h-12 text-black" />
            <h1 className="text-4xl font-bold tracking-tight">ParcelPilot AI</h1>
          </div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Select a persona below to experience the dual-context AI support system. 
            Access controls and source reliability are enforced dynamically based on your role.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Customers */}
          <div className="bg-white rounded-none border-2 border-black overflow-hidden">
            <div className="p-6 bg-white border-b-2 border-black flex items-center space-x-3">
              <UserIcon className="w-6 h-6 text-black" />
              <h2 className="text-xl font-semibold text-black">Customer View</h2>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-700 mb-6">
                Customers can only access their own account data and general policies. 
                Custom agreements automatically override general policies.
              </p>
              
              {customers.map((user) => (
                <button
                  key={user.username}
                  onClick={() => handleLogin(user.username)}
                  disabled={loginLoading !== null}
                  className="w-full flex items-center justify-between p-4 rounded-none border border-black hover:bg-black hover:text-white transition-all text-left group"
                >
                  <div>
                    <div className="font-medium text-black group-hover:text-white">
                      {user.name}
                    </div>
                    <div className="text-sm text-gray-500 group-hover:text-gray-300">
                      {user.account_id}
                    </div>
                  </div>
                  {loginLoading === user.username ? <Loader2 className="w-5 h-5 animate-spin text-white" /> : <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity">Login &rarr;</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Internal */}
          <div className="bg-white rounded-none border-2 border-black overflow-hidden">
            <div className="p-6 bg-white border-b-2 border-black flex items-center space-x-3">
              <ShieldAlert className="w-6 h-6 text-black" />
              <h2 className="text-xl font-semibold text-black">Internal Staff View</h2>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-700 mb-6">
                Staff have full access across all accounts, see source conflict flags, 
                and can access internal operations dashboards.
              </p>
              
              {internal.map((user) => (
                <button
                  key={user.username}
                  onClick={() => handleLogin(user.username)}
                  disabled={loginLoading !== null}
                  className="w-full flex items-center justify-between p-4 rounded-none border border-black hover:bg-black hover:text-white transition-all text-left group"
                >
                  <div>
                    <div className="font-medium text-black group-hover:text-white">
                      {user.name}
                    </div>
                    <div className="text-sm text-gray-500 group-hover:text-gray-300 capitalize">
                      {user.role.replace("_", " ")}
                    </div>
                  </div>
                  {loginLoading === user.username ? <Loader2 className="w-5 h-5 animate-spin text-white" /> : <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity">Login &rarr;</span>}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
