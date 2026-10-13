import { fileURLToPath } from "node:url";
import { config } from "dotenv";
import { PrismaMariaDb } from "@prisma/adapter-mariadb";
import { PrismaClient } from "./generated/prisma/client.js";

config({
  path: new URL("../../../private/database.env", import.meta.url),
  quiet: true,
});
export function createDatabase() {
  if (!process.env.DATABASE_URL) throw new Error("数据库连接尚未配置");
  const url = new URL(process.env.DATABASE_URL);
  const adapter = new PrismaMariaDb({
    host: url.hostname,
    port: Number(url.port || 3306),
    user: decodeURIComponent(url.username),
    password: decodeURIComponent(url.password),
    database: url.pathname.slice(1),
    connectionLimit: 5,
    // MySQL 8 caching_sha2_password needs the server key on a cold auth cache.
    cachingRsaPublicKey: process.env.DATABASE_RSA_PUBLIC_KEY ?? (
      url.hostname === "127.0.0.1" && url.port === "33084"
        ? fileURLToPath(new URL("../../../private/mysql84/public_key.pem", import.meta.url))
        : undefined
    ),
  });
  return new PrismaClient({ adapter });
}
