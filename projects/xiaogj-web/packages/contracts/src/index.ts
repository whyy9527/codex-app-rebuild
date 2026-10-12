import { initContract } from "@ts-rest/core";
import { z } from "zod";
const c = initContract();
const count = z.object({ label: z.string(), value: z.string() });
export const homeSnapshot = z.object({
  profile: z.object({
    greeting: z.string(),
    date: z.string(),
    campus: z.string(),
  }),
  todos: z.array(count.extend({ icon: z.string() })).min(1),
  quick: z.array(
    z.object({ label: z.string(), icon: z.string(), color: z.string() }),
  ),
  quickCatalog: z.array(
    z.object({ label: z.string(), icon: z.string(), color: z.string() }),
  ),
  metrics: z.array(
    count.extend({
      comparison: z.string(),
      tone: z.enum(["positive", "neutral"]),
    }),
  ),
  releases: z.array(
    z.object({ title: z.string(), date: z.string(), isNew: z.boolean() }),
  ),
  notices: z.array(
    z.object({ title: z.string(), date: z.string(), category: z.string() }),
  ),
  studentGroups: z.array(
    z.object({ label: z.string(), counts: z.array(count) }),
  ),
  studentPeriods: z.array(z.array(z.string()).length(6)).length(3),
  metricPeriods: z
    .array(
      z
        .array(
          z.object({
            comparison: z.string(),
            tone: z.enum(["neutral", "positive", "red"]),
            change: z.string().optional(),
            direction: z.literal("down").optional(),
          }),
        )
        .length(4),
    )
    .length(3),
  trend: z.object({
    dates: z.array(z.string()).length(7),
    schedule: z.array(z.array(z.number()).length(7)).length(2),
    income: z.array(z.array(z.number()).length(7)).length(2),
    attendance: z.array(z.array(z.number()).length(7)).length(2),
    summaries: z.array(z.array(z.string()).length(2)).length(3),
  }),
  donuts: z.array(
    z.object({
      title: z.string(),
      label: z.string(),
      total: z.number(),
      items: z.array(
        z.object({ label: z.string(), value: z.number(), color: z.string() }),
      ),
    }),
  ),
});
export type HomeSnapshot = z.infer<typeof homeSnapshot>;
export const api = c.router({
  health: {
    method: "GET",
    path: "/api/health",
    responses: { 200: z.object({ status: z.literal("ok") }) },
  },
  home: {
    method: "GET",
    path: "/api/home",
    responses: { 200: homeSnapshot, 503: z.object({ message: z.string() }) },
  },
});
