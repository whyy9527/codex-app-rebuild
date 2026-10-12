import { Controller, Module } from "@nestjs/common";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api, enrollmentSnapshot, enrollmentChoiceSnapshot } from "@xiaogj/contracts";
import { readFile } from "node:fs/promises";

@Controller()
class EnrollmentController {
  @TsRestHandler(api.enrollmentChoices)
  choices() {
    return tsRestHandler(api.enrollmentChoices, async ({ params }) => {
      try {
        const file = new URL("../../../../private/reference/enrollment-choices.json", import.meta.url);
        const actual = JSON.parse(await readFile(file, "utf8"));
        return { status: 200 as const, body: enrollmentChoiceSnapshot.parse(actual[params.kind]) };
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
