import { readFile } from "node:fs/promises";
import { studentsSnapshot } from "@xiaogj/contracts";
import { createDatabase } from "./database.js";

const snapshot = studentsSnapshot.parse(
  JSON.parse(
    await readFile(
      new URL("../../../private/reference/students-data.json", import.meta.url),
      "utf8",
    ),
  ),
);
const db = createDatabase();
try {
  await db.$transaction(async (tx) => {
    const id = "observed-students-baseline";
    const { rows, ...metadata } = snapshot;
    await tx.studentCapture.upsert({
      where: { id },
      create: { id, ...metadata },
      update: metadata,
    });
    await tx.student.deleteMany({ where: { captureId: id } });
    await tx.student.createMany({
      data: rows.map((row, position) => ({ ...row, position, captureId: id })),
    });
  });
  console.log(
    `Imported ${snapshot.rows.length} observed students; remaining records are not fabricated.`,
  );
} finally {
  await db.$disconnect();
}
