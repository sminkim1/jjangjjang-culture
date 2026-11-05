CREATE TABLE `refresh_courses` (
	`id` text PRIMARY KEY NOT NULL,
	`job` text NOT NULL,
	`provider` text NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `refresh_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`status` text NOT NULL,
	`started_at` text NOT NULL,
	`finished_at` text,
	`lease` integer DEFAULT 0 NOT NULL,
	`fence` integer DEFAULT 0 NOT NULL,
	`error` text
);
--> statement-breakpoint
CREATE TABLE `refresh_tasks` (
	`id` text PRIMARY KEY NOT NULL,
	`job` text NOT NULL,
	`provider` text NOT NULL,
	`payload` text NOT NULL,
	`status` text DEFAULT 'pending' NOT NULL,
	`attempts` integer DEFAULT 0 NOT NULL,
	`error` text
);
