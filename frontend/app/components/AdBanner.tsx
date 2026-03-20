"use client";

import { useEffect } from "react";

declare global {
  interface Window { adsbygoogle: unknown[] }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID;
const SLOT_ID = process.env.NEXT_PUBLIC_ADSENSE_SLOT_ID;

export default function AdBanner() {
  useEffect(() => {
    if (!CLIENT_ID || !SLOT_ID) return;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // adsbygoogle not ready yet
    }
  }, []);

  if (!CLIENT_ID || !SLOT_ID) return null;

  return (
    <div className="w-full my-4 overflow-hidden rounded-xl">
      <ins
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client={CLIENT_ID}
        data-ad-slot={SLOT_ID}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}
