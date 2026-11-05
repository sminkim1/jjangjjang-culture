import {sqliteTable,text,integer} from 'drizzle-orm/sqlite-core';
export const refreshJobs=sqliteTable('refresh_jobs',{id:text('id').primaryKey(),status:text('status').notNull(),startedAt:text('started_at').notNull(),finishedAt:text('finished_at'),lease:integer('lease').notNull().default(0),fence:integer('fence').notNull().default(0),error:text('error'),catalogKey:text('catalog_key')});
export const refreshTasks=sqliteTable('refresh_tasks',{id:text('id').primaryKey(),job:text('job').notNull(),provider:text('provider').notNull(),payload:text('payload').notNull(),status:text('status').notNull().default('pending'),attempts:integer('attempts').notNull().default(0),error:text('error')});
export const refreshCourses=sqliteTable('refresh_courses',{id:text('id').primaryKey(),job:text('job').notNull(),provider:text('provider').notNull(),payload:text('payload').notNull()});

export const refreshPages=sqliteTable('refresh_pages',{id:text('id').primaryKey(),signature:text('signature').notNull().unique()});
