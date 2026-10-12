import "reflect-metadata";
import { Controller, Module } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api } from "@xiaogj/contracts";
import { HomeModule } from "./home/home.module.js";
import { StudentsModule } from "./students/students.module.js";
@Controller()
class HealthController {
  @TsRestHandler(api.health)
  health() {
    return tsRestHandler(api.health, async () => ({
      status: 200,
      body: { status: "ok" as const },
    }));
  }
}
@Module({ imports: [HomeModule, StudentsModule], controllers: [HealthController] })
class AppModule {}
const app = await NestFactory.create(AppModule);
app.enableShutdownHooks();
await app.listen(Number(process.env.PORT ?? 3101), "127.0.0.1");
