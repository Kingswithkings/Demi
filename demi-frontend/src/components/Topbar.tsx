export default function Topbar() {
  return (
    <header className="h-20 border-b border-slate-800 flex items-center justify-between px-6">
      <div>
        <h2 className="text-xl font-semibold">Demi Command Center</h2>
        <p className="text-sm text-slate-400">
          Your AI planning, scheduling, and execution assistant
        </p>
      </div>

      <button className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-5 py-2 rounded-xl">
        New Task
      </button>
    </header>
  );
}