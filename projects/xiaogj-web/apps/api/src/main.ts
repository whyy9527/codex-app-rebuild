import "reflect-metadata";
import { Controller, Module } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api } from "@xiaogj/contracts";
import { HomeModule } from "./home/home.module.js";
import { StudentsModule } from "./students/students.module.js";
import { EnrollmentModule } from "./enrollment/enrollment.module.js";
import { AuthModule, Public } from "./auth/auth.module.js";
import cookieParser from "cookie-parser";
@Controller()
class HealthController {
  @Public()
  @TsRestHandler(api.health)
  health() {
    return tsRestHandler(api.health, async () => ({
      status: 200,
      body: { status: "ok" as const },
    }));
  }
}
@Module({ imports: [AuthModule, HomeModule, StudentsModule, EnrollmentModule], controllers: [HealthController] })
class AppModule {}
const app = await NestFactory.create(AppModule);
app.use(cookieParser());
app.enableShutdownHooks();
await app.listen(Number(process.env.PORT ?? 3101), "127.0.0.1");
