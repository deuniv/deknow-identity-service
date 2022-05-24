DROP TABLE IF EXISTS publication;

CREATE TABLE "publication" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "gsc_pub_id" TEXT,
    "title" TEXT NOT NULL,
    "link" TEXT,
    "authors" TEXT,
    "publication_date" TEXT,
    "source" TEXT,
    "description" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);