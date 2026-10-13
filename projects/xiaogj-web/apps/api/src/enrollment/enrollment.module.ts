import { Controller, Module } from "@nestjs/common";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api, enrollmentSnapshot, enrollmentChoiceSnapshot } from "@xiaogj/contracts";
import { readFile } from "node:fs/promises";

@Controller()
class EnrollmentController {
  @TsRestHandler(api.enrollmentChoices)
  choices() {
    return tsRestHandler(api.enrollmentChoices, async ({ params, query }) => {
      try {
        const file = new URL("../../../../private/reference/enrollment-choices.json", import.meta.url);
        const actual = JSON.parse(await readFile(file, "utf8"));
        const snapshot = enrollmentChoiceSnapshot.parse(actual[params.kind]);
        // The local catalog is representative data, not the source tenant's full count.
        const search = (query.search ?? "").trim().toLocaleLowerCase();
        const matching = snapshot.rows.map((row, index) => ({ row, badge: snapshot.presentation?.nameBadges[index] ?? null }))
          .filter(({ row }) => !search || row.slice(0, 1)
            .some(cell => cell.toLocaleLowerCase().includes(search)));
        const pageSize = query.pageSize ?? 10;
        const totalPages = Math.ceil(matching.length / pageSize);
        const page = Math.max(1, Math.min(query.page ?? 1, totalPages || 1));
        const visible = matching.slice((page - 1) * pageSize, page * pageSize);
        return { status: 200 as const, body: enrollmentChoiceSnapshot.parse({
          ...snapshot, rows: visible.map(item => item.row), total: matching.length, page, pageSize, totalPages,
          ...(snapshot.presentation ? { presentation: { ...snapshot.presentation, nameBadges: visible.map(item => item.badge) } } : {}),
        }) };
      } catch { return { status: 503 as const, body: { message: "报名目录观察数据尚未准备好" } }; }
    });
  }
  @TsRestHandler(api.enrollment)
  defaults() {
    return tsRestHandler(api.enrollment, async () => {
      try {
        const file = new URL("../../../../private/reference/enrollment-defaults.json", import.meta.url);
        const body = enrollmentSnapshot.parse(JSON.parse(await readFile(file, "utf8")));
        return { status: 200 as const, body };
      } catch {
        return { status: 503 as const, body: { message: "报名观察数据尚未准备好" } };
      }
    });
  }
}

@Module({ controllers: [EnrollmentController] })
export class EnrollmentModule {}
