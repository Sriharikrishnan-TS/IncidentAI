import Link from "next/link";

export default function HomePage() {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-semibold">IncidentOS Frontend</h1>
      <p className="text-slate-300">Starter App Router shell for hackathon development.</p>
      <Link href="/dashboard" className="underline">
        Open dashboard
      </Link>
    </section>
  );
}
