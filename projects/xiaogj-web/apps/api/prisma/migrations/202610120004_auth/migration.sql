CREATE TABLE `AuthUser` (
  `id` VARCHAR(80) NOT NULL,
  `username` VARCHAR(200) NOT NULL,
  `displayName` VARCHAR(200) NOT NULL,
  `passwordHash` VARCHAR(100) NOT NULL,
  `active` BOOLEAN NOT NULL DEFAULT true,
  UNIQUE INDEX `AuthUser_username_key`(`username`),
  PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE TABLE `AuthSession` (
  `id` VARCHAR(80) NOT NULL,
  `userId` VARCHAR(80) NOT NULL,
  `expiresAt` DATETIME(3) NOT NULL,
  INDEX `AuthSession_userId_idx`(`userId`),
  PRIMARY KEY (`id`),
  CONSTRAINT `AuthSession_userId_fkey` FOREIGN KEY (`userId`) REFERENCES `AuthUser`(`id`) ON DELETE CASCADE ON UPDATE CASCADE
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
