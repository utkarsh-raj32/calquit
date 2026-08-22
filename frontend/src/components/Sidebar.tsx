"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Package, MessageSquare, Activity, LogOut, User as UserIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { auth, type UserContext } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserContext | null>(null);

  useEffect(() => {
    setUser(auth.getUser());
  }, []);

  const handleLogout = () => {
    auth.logout();
    router.push("/");
  };

  if (!user) return null;

  const isCustomer = user.role === "customer";
  
  const navItems = isCustomer 
    ? [
        { name: "Support Chat", href: "/customer", icon: MessageSquare },
      ]
    : [
        { name: "Internal Agent", href: "/internal", icon: MessageSquare },
        { name: "Ops Dashboard", href: "/dashboard", icon: Activity },
      ];

  return (
    <div className="w-64 bg-black text-white flex flex-col h-screen border-r-2 border-black">
      <div className="p-6 flex items-center space-x-3 text-white">
        <Package className="w-8 h-8 text-white" />
        <span className="text-xl font-bold tracking-tight">ParcelPilot</span>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-4 py-3 rounded-none transition-colors border border-transparent",
                isActive 
                  ? "bg-white text-black border-white" 
                  : "text-gray-400 hover:bg-white hover:text-black hover:border-white"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t-2 border-white mt-auto">
        <div className="flex items-center space-x-3 mb-4 px-2">
          <div className="w-8 h-8 rounded-none border border-white flex items-center justify-center text-white">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="flex flex-col text-sm">
            <span className="text-white font-medium truncate">{user.name}</span>
            <span className="text-gray-400 text-xs truncate capitalize">{user.role.replace("_", " ")}</span>
          </div>
        </div>
        
        <button 
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-4 py-2 text-sm rounded-none text-gray-400 hover:text-black hover:bg-white transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
