import { Controller, Module, Injectable, Inject, SetMetadata, UnauthorizedException, ForbiddenException, type CanActivate, type ExecutionContext, type OnModuleDestroy, Req, Res } from "@nestjs/common";
import { APP_GUARD, Reflector } from "@nestjs/core";
import { JwtModule, JwtService } from "@nestjs/jwt";
import { TsRestHandler, tsRestHandler } from "@ts-rest/nest";
import { api } from "@xiaogj/contracts";
import { compare, hash } from "bcryptjs";
import { randomUUID } from "node:crypto";
import { config } from "dotenv";
import type { Request, Response } from "express";
import { createDatabase } from "../database.js";

config({ path: new URL("../../../../private/auth.env", import.meta.url), quiet: true });
export const Public = () => SetMetadata("public", true);
const cookieName = "xiaogj_session";
const cookieOptions = { httpOnly: true, sameSite: "lax" as const, secure: process.env.NODE_ENV === "production", path: "/" };
type AuthRequest = Request & { auth?: { id: string; username: string; displayName: string }; sessionId?: string };

@Injectable()
class AuthService implements OnModuleDestroy {
  private db = createDatabase();
  private dummyHash = hash(randomUUID(), 12);
  constructor(@Inject(JwtService) private jwt: JwtService) {}
  async onModuleDestroy() { await this.db.$disconnect(); }
  async signIn(username: string, password: string) {
    const user = await this.db.authUser.findUnique({ where: { username } });
    const valid = await compare(password, user?.passwordHash ?? await this.dummyHash);
    if (!user?.active || !valid) return null;
    const session = await this.db.authSession.create({ data: {
      id: randomUUID(), userId: user.id, expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000),
    } });
    const token = await this.jwt.signAsync({ sub: user.id, sid: session.id });
    return { token, user: { id: user.id, username: user.username, displayName: user.displayName } };
  }
  async authenticate(token: string) {
    try {
      const payload = await this.jwt.verifyAsync<{ sub: string; sid: string }>(token);
      if (typeof payload.sub !== "string" || typeof payload.sid !== "string") return null;
      const session = await this.db.authSession.findUnique({ where: { id: payload.sid }, include: { user: true } });
      if (!session || session.userId !== payload.sub || !session.user.active || session.expiresAt.getTime() <= Date.now()) return null;
      return { sessionId: session.id, user: { id: session.user.id, username: session.user.username, displayName: session.user.displayName } };
    } catch { return null; }
  }
  async logout(sessionId: string) { await this.db.authSession.deleteMany({ where: { id: sessionId } }); }
}

@Injectable()
class AuthGuard implements CanActivate {
  constructor(@Inject(Reflector) private reflector: Reflector, @Inject(AuthService) private auth: AuthService) {}
  async canActivate(context: ExecutionContext) {
    const request = context.switchToHttp().getRequest<AuthRequest>();
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method) && request.get("origin") !== process.env.AUTH_ORIGIN) {
      throw new ForbiddenException("请求来源不允许");
    }
    if (this.reflector.getAllAndOverride<boolean>("public", [context.getHandler(), context.getClass()])) return true;
    const token = request.cookies?.[cookieName];
    const actual = typeof token === "string" ? await this.auth.authenticate(token) : null;
    if (!actual) throw new UnauthorizedException("请先登录");
    request.auth = actual.user;
    request.sessionId = actual.sessionId;
    return true;
  }
}

@Controller()
class AuthController {
  constructor(@Inject(AuthService) private auth: AuthService) {}
  @Public()
  @TsRestHandler(api.login)
  login(@Res({ passthrough: true }) response: Response) {
    return tsRestHandler(api.login, async ({ body }) => {
      const actual = await this.auth.signIn(body.username, body.password);
      if (!actual) return { status: 401 as const, body: { message: "用户名或密码错误" } };
      response.cookie(cookieName, actual.token, { ...cookieOptions, maxAge: 8 * 60 * 60 * 1000 });
      return { status: 200 as const, body: actual.user };
    });
  }
  @TsRestHandler(api.session)
  session(@Req() request: AuthRequest) {
    return tsRestHandler(api.session, async () => ({ status: 200 as const, body: request.auth! }));
  }
  @TsRestHandler(api.logout)
  logout(@Req() request: AuthRequest, @Res({ passthrough: true }) response: Response) {
    return tsRestHandler(api.logout, async () => {
      await this.auth.logout(request.sessionId!);
      response.clearCookie(cookieName, cookieOptions);
      return { status: 200 as const, body: { status: "ok" as const } };
    });
  }
}

@Module({
  imports: [JwtModule.registerAsync({ useFactory: () => {
    const secret = process.env.JWT_SECRET;
    if (!secret || Buffer.byteLength(secret) < 32 || !process.env.AUTH_ORIGIN) throw new Error("Authentication configuration is missing");
    return { secret, signOptions: { algorithm: "HS256", expiresIn: "8h", issuer: "xiaogj-local", audience: "xiaogj-web" }, verifyOptions: { algorithms: ["HS256"], issuer: "xiaogj-local", audience: "xiaogj-web" } };
  } })],
  controllers: [AuthController], providers: [AuthService, { provide: APP_GUARD, useClass: AuthGuard }],
})
export class AuthModule {}
