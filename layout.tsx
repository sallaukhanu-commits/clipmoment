import type { Metadata } from "next";
import "./globals.css";
import { APP_NAME } from "@/lib/config";

export const metadata: Metadata = {
  title: `${APP_NAME} — Turn long videos into their best moments`,
  description: "Upload a podcast or interview and get captioned, vertical short-form clip candidates ranked by estimated engagement.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
