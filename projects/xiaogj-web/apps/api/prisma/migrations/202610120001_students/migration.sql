-- CreateTable
CREATE TABLE `StudentCapture` (
    `id` VARCHAR(80) NOT NULL,
    `total` INTEGER NOT NULL,
    `page` INTEGER NOT NULL,
    `pageSize` INTEGER NOT NULL,
    `pages` INTEGER NOT NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `Student` (
    `id` VARCHAR(80) NOT NULL,
    `name` VARCHAR(200) NOT NULL,
    `account` VARCHAR(200) NOT NULL,
    `number` VARCHAR(80) NOT NULL,
    `identity` VARCHAR(80) NOT NULL,
    `phone` VARCHAR(80) NOT NULL,
    `englishName` VARCHAR(200) NOT NULL,
    `card` VARCHAR(80) NOT NULL,
    `school` VARCHAR(200) NOT NULL,
    `status` VARCHAR(80) NOT NULL,
    `gender` VARCHAR(20) NOT NULL,
    `position` INTEGER NOT NULL,
    `captureId` VARCHAR(80) NOT NULL,

    INDEX `Student_captureId_position_idx`(`captureId`, `position`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `Student` ADD CONSTRAINT `Student_captureId_fkey` FOREIGN KEY (`captureId`) REFERENCES `StudentCapture`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
