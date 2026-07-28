import KpiTicker from "./components/KpiTicker";
import FlightMap from "./components/FlightMap";
import DelayChart from "./components/DelayChart";
import CopilotDrawer from "./components/CopilotDrawer";

export default function DashboardPage() {
  return (
    <main className="p-6 space-y-6">
      <h1 className="text-xl font-semibold">Aviation Control Tower</h1>
      <KpiTicker />
      <FlightMap />
      <DelayChart />
      <CopilotDrawer />
    </main>
  );
}
