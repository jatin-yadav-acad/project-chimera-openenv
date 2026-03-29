"use client";

import ExploitVisualizer from "@/components/ExploitVisualizer";
import { useState } from "react";
import { Activity, ShieldAlert, Database, ServerCrash, Cpu } from "lucide-react";

export default function Page() {
  const [testStatus, setTestStatus] = useState<string>("Idle");

  const runTestAttack = async (type: "sync" | "async") => {
    setTestStatus(`Deploying ${type} assault payload...`);
    
    // First reset the DB
    await fetch("/api/reset", { method: "POST" });
    
    // Payload generation
    let payload = [];
    if (type === "sync") {
      // Normal test: One withdrawal, no race condition window hit
      payload = ["WITHDRAW 1000", "GET BALANCE"];
    } else {
      // Race Condition Vulnerability Hit
      // Two identical concurrent withdrawals designed to hit the TOCTOU window
      payload = ["WITHDRAW 1000", "WITHDRAW 1000", "WITHDRAW 1000", "WITHDRAW 1000"];
    }

    try {
      const res = await fetch("/api/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "exploit",
          payload_sequence: payload
        })
      });
      const data = await res.json();
      setTestStatus(data.reward === 1.0 ? "CRITICAL: Race Exploit Succeeded!" : "Access Denied: Sync Handled.");
    } catch (err) {
      setTestStatus("Error connecting to Engine.");
    }
  };

  return (
    <main className="min-h-screen bg-[#0a0a0c] text-white p-8 grid grid-cols-12 gap-6 items-start font-mono">
      {/* Sidebar Controls */}
      <aside className="col-span-12 md:col-span-3 lg:col-span-3 border border-gray-800 rounded-lg p-6 bg-black flex flex-col gap-8 shadow-2xl relative">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <ShieldAlert size={80} />
        </div>
        
        <div>
          <h1 className="text-3xl font-black uppercase text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-600 mb-1 z-10 relative">
            CHIMERA
          </h1>
          <p className="text-gray-500 text-xs tracking-widest uppercase">
            OpenEnv Threat Simulator
          </p>
        </div>

        <div className="space-y-4 z-10">
          <h3 className="text-sm text-gray-400 border-b border-gray-800 pb-2 flex items-center gap-2">
            <Activity size={14} /> Agent Control Deck
          </h3>
          
          <button 
            onClick={() => runTestAttack("sync")}
            className="w-full text-left p-3 rounded bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-blue-500 transition-colors group flex items-start gap-3"
          >
            <div className="p-2 bg-gray-800 rounded group-hover:bg-blue-900">
              <Database size={16} className="text-gray-400 group-hover:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-200">Standard Probe</p>
              <p className="text-xs text-gray-500 mt-1">Single Thread Withdrawal</p>
            </div>
          </button>

          <button 
            onClick={() => runTestAttack("async")}
            className="w-full text-left p-3 rounded bg-gray-900 hover:bg-red-900/20 border border-gray-800 hover:border-red-500 transition-colors group flex items-start gap-3"
          >
            <div className="p-2 bg-gray-800 rounded group-hover:bg-red-900/50">
              <ServerCrash size={16} className="text-gray-400 group-hover:text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-200 uppercase tracking-widest text-red-500">Run TOCTOU Exploit</p>
              <p className="text-xs text-gray-500 mt-1 opacity-80">Flood asynchronous read/write locks heavily.</p>
            </div>
          </button>
        </div>

        {/* Engine Status Block */}
        <div className="mt-auto pt-6 border-t border-gray-800">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500 flex items-center gap-2"><Cpu size={12} /> Target Memory: Active</span>
            <span className="text-green-500 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Secure Port
            </span>
          </div>
          <div className="mt-4 p-3 bg-gray-900 rounded font-mono text-xs text-gray-300 border border-gray-800 shadow-inner">
            <span className="text-blue-500">sys&gt;</span> {testStatus}
          </div>
        </div>
      </aside>

      {/* Main Visualization Pane */}
      <section className="col-span-12 md:col-span-9 lg:col-span-9 h-[calc(100vh-4rem)]">
        <ExploitVisualizer />
      </section>
    </main>
  );
}
