import { Controller } from "@nestjs/common";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api, homeSnapshot, recentClassesSnapshot } from "@xiaogj/contracts";
import { readFile } from "node:fs/promises";
@Controller()
export class HomeController {
  @TsRestHandler(api.recentClasses)
  recentClasses() {
    return tsRestHandler(api.recentClasses, async () => {
      try {
        const file = new URL("../../../../private/reference/recent-classes.json", import.meta.url);
        const body = recentClassesSnapshot.parse(JSON.parse(await readFile(file, "utf8")));
        return { status: 200 as const, body };
      } catch {
        return { status: 503 as const, body: { message: "近期开班观察数据尚未准备好" } };
      }
    });
  }
  @TsRestHandler(api.home)
  home() {
    return tsRestHandler(api.home, async () => {
      try {
        const file = new URL(
          "../../../../private/reference/home-data.json",
          import.meta.url,
        );
        const body = homeSnapshot.parse(
          JSON.parse(await readFile(file, "utf8")),
        );
        return { status: 200 as const, body };
      } catch {
        return {
          status: 503 as const,
          body: { message: "本地观察数据尚未准备好" },
        };
      }
    });
  }
}
