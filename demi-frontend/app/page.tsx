import ChatPanel from "@/components/ChatPanel";
import LogsPanel from "@/components/LogsPanel";
import PendingPanel from "@/components/PendingPanel";
import Topbar from "@/components/Topbar";
import UpcomingPanel from "@/components/UpcomingPanel";

const navItems = ["Chat", "Upcoming", "Pending", "Logs", "Settings"];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-800 bg-slate-900 p-6 md:flex md:flex-col">
          <h1 className="text-2xl font-bold text-emerald-400">Demi</h1>
          <p className="mt-1 text-sm text-slate-400">Ask, confirm, act</p>

          <nav className="mt-10 space-y-2">
            {navItems.map((item) => (
              <button
                key={item}
                className="w-full rounded-lg px-4 py-3 text-left text-sm text-slate-300 hover:bg-slate-800"
                type="button"
              >
                {item}
              </button>
            ))}
          </nav>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <Topbar />

          <div className="grid flex-1 gap-6 p-4 md:p-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            <ChatPanel />

            <div className="space-y-6">
              <UpcomingPanel />
              <PendingPanel />
              <LogsPanel />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
