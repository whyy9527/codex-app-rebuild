import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const origin = "http://127.0.0.1:5183";
const base = "http://127.0.0.1:3101";
const credentials = JSON.parse(await readFile(new URL("../../../../private/local-auth.json", import.meta.url), "utf8"));
const post = (path, body, cookie, requestOrigin = origin) => fetch(base + path, {
  method: "POST", headers: { "content-type": "application/json", origin: requestOrigin, ...(cookie ? { cookie } : {}) }, body: JSON.stringify(body),
});

test("business APIs reject anonymous users; health stays available", async () => {
  for (const path of ["/api/auth/session", "/api/home", "/api/home/recent-classes", "/api/students", "/api/students/example/detail", "/api/enrollment/defaults", "/api/enrollment/choices/courses", "/api/enrollment/choices/items"]) {
    assert.equal((await fetch(base + path)).status, 401, path);
  }
  assert.equal((await fetch(base + "/api/health")).status, 200);
});
test("invalid credentials, malformed input and foreign origin cannot create a session", async () => {
  const bad = await post("/api/auth/login", { username: credentials.username, password: "invalid-test-password" });
  assert.equal(bad.status, 401); assert.equal(bad.headers.get("set-cookie"), null);
  assert.equal((await post("/api/auth/login", {})).status, 400);
  assert.equal((await post("/api/auth/login", credentials, undefined, "https://foreign.invalid")).status, 403);
});
test("cookie authenticates persisted session and logout revokes a copied token", async () => {
  const login = await post("/api/auth/login", { username: credentials.username, password: credentials.password });
  assert.equal(login.status, 200);
  const user = await login.json(); assert.equal(user.username, credentials.username); assert.equal(user.passwordHash, undefined);
  const header = login.headers.get("set-cookie");
  assert.match(header, /HttpOnly/i); assert.match(header, /SameSite=Lax/i); assert.match(header, /Path=\//i);
  const cookie = header.split(";")[0];
  try {
    assert.equal((await fetch(base + "/api/auth/session", { headers: { cookie } })).status, 200);
    assert.equal((await fetch(base + "/api/students", { headers: { cookie } })).status, 200);
    const catalogs = JSON.parse(await readFile(new URL("../../../../private/reference/enrollment-choices.json", import.meta.url), "utf8"));
    for (const kind of ["courses", "items"]) {
      const response = await fetch(base + "/api/enrollment/choices/" + kind, { headers: { cookie } });
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), catalogs[kind]);
    }
    assert.equal((await post("/api/auth/logout", {}, cookie, "https://foreign.invalid")).status, 403);
    assert.equal((await fetch(base + "/api/auth/session", { headers: { cookie } })).status, 200);
  } finally { assert.equal((await post("/api/auth/logout", {}, cookie)).status, 200); }
  assert.equal((await fetch(base + "/api/auth/session", { headers: { cookie } })).status, 401);
  assert.equal((await fetch(base + "/api/home", { headers: { cookie: "xiaogj_session=invalid.token.value" } })).status, 401);
});
