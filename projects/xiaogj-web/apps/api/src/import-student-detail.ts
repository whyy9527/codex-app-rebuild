import { readFile } from "node:fs/promises";
import { studentDetailSnapshot } from "@xiaogj/contracts";
import { createDatabase } from "./database.js";

const capture = JSON.parse(await readFile(new URL("../../../private/reference/student-detail.json", import.meta.url), "utf8"));
const data = studentDetailSnapshot.parse(capture.data);
const db = createDatabase();
try {
  const student = await db.student.findUniqueOrThrow({ where: { id: data.id } });
  if (student.name !== data.name) throw new Error("Detail capture does not match imported student");
  await db.studentDetail.upsert({
    where: { studentId: data.id },
    create: { studentId: data.id, data, observedAt: new Date(capture.observedAt), provenance: capture.provenance },
    update: { data, observedAt: new Date(capture.observedAt), provenance: capture.provenance },
  });
  console.log("Imported one observed student detail");
} finally { await db.$disconnect(); }
