import { FootballLab } from "@/components/FootballLab";
import dataset from "@/public/data/football-lab.json";
import type { FootballLabData } from "@/types/analytics";

export default function Page() {
  return <FootballLab initialData={dataset as FootballLabData} />;
}
