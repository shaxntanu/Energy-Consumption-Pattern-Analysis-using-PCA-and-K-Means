import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Energy Consumption Clustering",
  description: "PCA + K-Means analysis of energy consumption patterns",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
