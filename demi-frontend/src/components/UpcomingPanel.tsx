export default function UpcomingPanel() {
  return (
    <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <h3 className="font-semibold mb-4">Upcoming</h3>

      <div className="space-y-3">
        <div className="bg-slate-800 rounded-xl p-4">
          <p className="font-medium">Meeting with client</p>
          <p className="text-sm text-slate-400">Tomorrow · 10:00 AM</p>
        </div>

        <div className="bg-slate-800 rounded-xl p-4">
          <p className="font-medium">Review Demi roadmap</p>
          <p className="text-sm text-slate-400">Friday · 2:00 PM</p>
        </div>
      </div>
    </section>
  );
}