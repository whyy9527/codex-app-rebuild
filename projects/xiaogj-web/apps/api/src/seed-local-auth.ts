import { randomBytes, randomUUID } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { hash } from "bcryptjs";
import { createDatabase } from "./database.js";

const privateFile = new URL("../../../private/local-auth.json", import.meta.url);
let user: { id: string; username: string; password: string };
try { user = JSON.parse(await readFile(privateFile, "utf8")); }
catch (error) {
  if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  user = { id: randomUUID(), username: "local@rebuild", password: randomBytes(24).toString("base64url") };
  await writeFile(privateFile, JSON.stringify(user), { mode: 0o600, flag: "wx" });
}
try {
  await writeFile(new URL("../../../private/auth.env", import.meta.url),
    `JWT_SECRET=${randomBytes(48).toString("hex")}\nAUTH_ORIGIN=http://127.0.0.1:5183\n`, { mode: 0o600, flag: "wx" });
} catch (error) { if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error; }
const db = createDatabase();
try {
  await db.authUser.upsert({ where: { username: user.username },
    create: { id: user.id, username: user.username, displayName: "本地验收账号", passwordHash: await hash(user.password, 12) }, update: {} });
  console.log("Local verification account prepared; credentials remain in the private file.");
} finally { await db.$disconnect(); }
