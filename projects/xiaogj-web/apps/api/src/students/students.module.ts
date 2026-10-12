import { Controller, Module, type OnModuleDestroy } from "@nestjs/common";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api, studentsSnapshot, studentDetailSnapshot } from "@xiaogj/contracts";
import { createDatabase } from "../database.js";

@Controller()
class StudentsController implements OnModuleDestroy {
  private db?: ReturnType<typeof createDatabase>;
  async onModuleDestroy() {
    await this.db?.$disconnect();
  }
  @TsRestHandler(api.studentDetail)
  studentDetail() {
    return tsRestHandler(api.studentDetail, async ({ params }) => {
      try {
        this.db ??= createDatabase();
        const record = await this.db.studentDetail.findUnique({ where: { studentId: params.id } });
        if (!record) throw new Error("missing detail capture");
        const body = studentDetailSnapshot.parse(record.data);
        if (body.id !== params.id) throw new Error("detail identity mismatch");
        return { status: 200 as const, body };
      } catch {
        return { status: 503 as const, body: { message: "学员详情暂时无法读取" } };
      }
    });
  }
  @TsRestHandler(api.students)
  students() {
    return tsRestHandler(api.students, async ({ query }) => {
      try {
        this.db ??= createDatabase();
        const capture = await this.db.studentCapture.findUnique({
          where: { id: "observed-students-baseline" },
        });
        if (!capture) throw new Error("missing capture");
        const imported = await this.db.student.count({ where: { captureId: capture.id } });
        if (imported !== capture.total) throw new Error("incomplete capture");
        const where = {
          captureId: capture.id,
          ...(query.search ? { OR: [
            { number: { contains: query.search } },
            { phone: { contains: query.search } },
            { name: { contains: query.search } },
          ] } : {}),
        };
        const [total, rows] = await this.db.$transaction([
          this.db.student.count({ where }),
          this.db.student.findMany({ where, orderBy: { position: "asc" },
            skip: (query.page - 1) * capture.pageSize, take: capture.pageSize }),
        ]);
        const body = studentsSnapshot.parse({
          total, page: query.page, pageSize: capture.pageSize,
          pages: Math.max(1, Math.ceil(total / capture.pageSize)), rows,
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
