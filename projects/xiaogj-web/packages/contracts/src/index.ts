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
export const studentsSnapshot = z.object({
  rows: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      account: z.string(),
      number: z.string(),
      identity: z.string(),
      phone: z.string(),
      englishName: z.string(),
      card: z.string(),
      school: z.string(),
      status: z.string(),
      gender: z.enum(["male", "female", "unknown"]),
    }),
  ),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  pageSize: z.number().int().positive(),
  pages: z.number().int().positive(),
});
export type StudentsSnapshot = z.infer<typeof studentsSnapshot>;
const detailField = z.object({ label: z.string(), value: z.string(), emphasis: z.boolean().optional() });
const detailTabTable = z.object({
  headers: z.array(z.array(z.string())), rows: z.array(z.array(z.string())),
  emptyText: z.string().optional(),
  pagination: z.object({ total: z.number().int(), page: z.number().int(), pages: z.number().int(), pageSize: z.number().int() }).optional(),
});
const studentBusinessTabs = z.object({
  tuition: z.object({ table: detailTabTable, showDetails: z.boolean(), includeZero: z.boolean() }),
  consumption: z.object({ table: detailTabTable, preset: z.string(), startDate: z.string(), endDate: z.string(), type: z.string(), course: z.string() }),
  points: z.object({ table: detailTabTable, rule: z.string(), timePreset: z.string(), startDate: z.string(), endDate: z.string(), add: z.boolean(), subtract: z.boolean(), cleared: z.boolean() }),
});
export const studentDetailSnapshot = z.object({
  id: z.string(), name: z.string(), status: z.string(),
  gender: z.enum(["male", "female", "unknown"]), tag: z.string(),
  photoSrc: z.string().nullable(),
  businessTabs: studentBusinessTabs.optional(),
  summary: z.array(detailField),
  sections: z.array(z.object({ title: z.string(), fields: z.array(detailField) })),
  tabs: z.array(z.string()),
  classes: z.object({ headers: z.array(z.string()), rows: z.array(z.array(z.string())) }),
});
export type StudentDetailSnapshot = z.infer<typeof studentDetailSnapshot>;
// Blank enrollment defaults from an actual observation, not a synthetic tenant.
export const enrollmentSnapshot = z.object({
  accountSuffix: z.string().min(1),
  paymentDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  attributionDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  observedAt: z.string().datetime(),
});
export const recentClassesSnapshot = z.object({
  summary: z.string(),
  headers: z.array(z.string()).length(4),
  rows: z.array(z.array(z.string()).length(4)).max(6),
  observedAt: z.string().datetime(),
});
const authUser = z.object({ id: z.string(), username: z.string(), displayName: z.string() });
const unauthorized = z.object({ message: z.string() }).passthrough();
export const api = c.router({
  login: { method: "POST", path: "/api/auth/login", body: z.object({
    username: z.string().min(1).max(200),
    password: z.string().min(1).max(50).refine(value => new TextEncoder().encode(value).length <= 72),
  }), responses: { 200: authUser, 401: unauthorized } },
  session: { method: "GET", path: "/api/auth/session", responses: { 200: authUser, 401: unauthorized } },
  logout: { method: "POST", path: "/api/auth/logout", body: z.object({}), responses: { 200: z.object({ status: z.literal("ok") }), 401: unauthorized } },
  recentClasses: {
    method: "GET",
    path: "/api/home/recent-classes",
    responses: { 401: unauthorized, 200: recentClassesSnapshot, 503: z.object({ message: z.string() }) },
  },
  enrollment: {
    method: "GET",
    path: "/api/enrollment/defaults",
    responses: { 401: unauthorized, 200: enrollmentSnapshot, 503: z.object({ message: z.string() }) },
  },
  studentDetail: {
    method: "GET",
    path: "/api/students/:id/detail",
    pathParams: z.object({ id: z.string().min(1) }),
    responses: { 401: unauthorized, 200: studentDetailSnapshot, 503: z.object({ message: z.string() }) },
  },
  students: {
    method: "GET",
    path: "/api/students",
    query: z.object({
      page: z.coerce.number().int().positive().default(1),
      search: z.string().default(""),
    }),
    responses: {
      401: unauthorized,
      200: studentsSnapshot,
      503: z.object({ message: z.string() }),
    },
  },
  health: {
    method: "GET",
    path: "/api/health",
    responses: { 200: z.object({ status: z.literal("ok") }) },
  },
  home: {
    method: "GET",
    path: "/api/home",
    responses: { 401: unauthorized, 200: homeSnapshot, 503: z.object({ message: z.string() }) },
  },
});
