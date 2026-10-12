import { Controller, Module, type OnModuleDestroy } from "@nestjs/common";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api, studentsSnapshot } from "@xiaogj/contracts";
import { createDatabase } from "../database.js";

@Controller()
class StudentsController implements OnModuleDestroy {
  private db?: ReturnType<typeof createDatabase>;
  async onModuleDestroy() {
    await this.db?.$disconnect();
  }
  @TsRestHandler(api.students)
  students() {
    return tsRestHandler(api.students, async ({ query }) => {
      if (query.page !== 1 || query.search !== "") {
        return {
          status: 503 as const,
          body: { message: "该查询的学员数据尚未准备好" },
        };
      }
      try {
        this.db ??= createDatabase();
        const capture = await this.db.studentCapture.findUnique({
          where: { id: "observed-students-baseline" },
          include: { students: { orderBy: { position: "asc" } } },
        });
        if (!capture) throw new Error("missing capture");
        const body = studentsSnapshot.parse({
          ...capture,
          rows: capture.students,
        });
        return { status: 200 as const, body };
      } catch {
        return {
          status: 503 as const,
          body: { message: "学员数据尚未准备好" },
        };
      }
    });
  }
}
@Module({ controllers: [StudentsController] })
export class StudentsModule {}
