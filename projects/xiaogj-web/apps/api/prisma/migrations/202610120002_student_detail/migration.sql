CREATE TABLE `StudentDetail` (
  `studentId` VARCHAR(80) NOT NULL,
  `data` JSON NOT NULL,
  `observedAt` DATETIME(3) NOT NULL,
  `provenance` VARCHAR(500) NOT NULL,
  PRIMARY KEY (`studentId`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE `StudentDetail` ADD CONSTRAINT `StudentDetail_studentId_fkey`
  FOREIGN KEY (`studentId`) REFERENCES `Student`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
