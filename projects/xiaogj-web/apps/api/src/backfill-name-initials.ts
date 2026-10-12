import { createDatabase } from "./database.js";
import { studentNameInitials } from "./students/name-initials.js";

const db = createDatabase();
try {
  const rows = await db.student.findMany({ select: { id: true, name: true } });
  await db.$transaction(rows.map(row => db.student.update({
    where: { id: row.id },
    data: { nameInitials: studentNameInitials(row.name) },
  })));
  console.log(`Updated name search initials for ${rows.length} students.`);
} finally {
  await db.$disconnect();
}
