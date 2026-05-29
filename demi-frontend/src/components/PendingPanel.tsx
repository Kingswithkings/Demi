export default function PendingPanel() {
  return (
    <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <h3 className="font-semibold mb-4">Pending Confirmations</h3>

      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
        <p className="font-medium text-amber-300">Confirm calendar event?</p>
        <p className="text-sm text-slate-400 mt-1">
          Demi needs approval before creating this event.
        </p>

        <div className="flex gap-2 mt-4">
          <button className="bg-emerald-500 text-slate-950 px-4 py-2 rounded-lg text-sm font-semibold">
            Confirm
          </button>
          <button className="bg-slate-800 px-4 py-2 rounded-lg text-sm">
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}