CREATE TABLE `refresh_pages` (
	`id` text PRIMARY KEY NOT NULL,
	`signature` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `refresh_pages_signature_unique` ON `refresh_pages` (`signature`);