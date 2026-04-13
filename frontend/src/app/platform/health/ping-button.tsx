"use client";

import { useState } from "react";
import { runtimeApi } from "@/lib/api";

export function CachePingButton() {
  const [status, setStatus] = useState<string>("idle");

  async function onPing() {
    setStatus("running");
    const payload = await runtimeApi.cachePing();
    setStatus(`${payload.status} via ${payload.backend}`);
  }

  return <button onClick={onPing}>Ping cache ({status})</button>;
}
