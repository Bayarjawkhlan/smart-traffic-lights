import { SIM_URL } from "../config";
import { requestJson } from "./http";
import type { ControlCommand, ExperimentsResponse, Network, SimState } from "./types";

export const fetchNetwork = () => requestJson<Network>(`${SIM_URL}/api/network`);

export const sendControl = (command: ControlCommand) =>
  requestJson<SimState>(`${SIM_URL}/api/control`, { method: "POST", body: JSON.stringify(command) });

export const requestExplanation = (site: string, language: "en" | "mn") =>
  requestJson<{ text: string; t: number }>(`${SIM_URL}/api/explain`, {
    method: "POST",
    body: JSON.stringify({ site, language }),
  });

export const fetchExperiments = () => requestJson<ExperimentsResponse>(`${SIM_URL}/api/experiments`);

export const startExperiments = (scenarios: string[], duration: number) =>
  requestJson<{ running: boolean }>(`${SIM_URL}/api/experiments`, {
    method: "POST",
    body: JSON.stringify({ scenarios, duration }),
  });
