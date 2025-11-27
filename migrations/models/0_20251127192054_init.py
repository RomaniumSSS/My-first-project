from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "username" VARCHAR(255),
    "first_name" VARCHAR(255),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_telegra_ab91e9" ON "users" ("telegram_id");
CREATE TABLE IF NOT EXISTS "goals" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "image_base64" TEXT,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "checkins" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "date" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "report_text" TEXT NOT NULL,
    "ai_feedback" TEXT,
    "goal_id" INT NOT NULL REFERENCES "goals" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmV9v2jAQwL8KytMmbRWlULq9AaMtawtTS7dpVRWZxASLxKaO0xZNfPfZJokTEzIyMQ"
    "RV3sL9SXw/23dn89vwiA1d/6gzgda0h43Pld8GBh7kD7rqQ8UAs5lSCAEDI1faWsIIYSkE"
    "I59RYDEuHwPXh1xkQ9+iaMYQEZ/AgesKIbG4IcKOEgUYPQXQZMSBbAIpVzw8cjHCNnyFfv"
    "RzNjXHCLp2arTIFt+WcpPNZ1LWw+xcGoqvjUyLuIGHlfFsziYEx9YIMyF1IIYUMChez2gg"
    "hi9GF0YaRbQcqTJZDjHhY8MxCFyWCHdDBhbBgh8fjS8DdMRXPtaO68362clp/YybyJHEku"
    "ZiGZ6KfekoCfSHxkLqAQNLC4lRceMKuEruC5cy5MFsfJGPBtAOnY6iBx1nBC+PZyRQQNUi"
    "2hJRCoE9wO48nKwcfMPeTfdu2Lr5JiLxfP/JlXBaw67Q1KR0rknfnb4XcsK3wHJvxC+p/O"
    "gNLyviZ+XXoN+VBInPHCq/qOyGvwwxJhAwYmLyYgI7sa4iaQSGW6rJpHBGKDMZfGWrczrk"
    "0uz51Ny0aeXs9nMi8yau+3OYmrP+99Zt57J1++6m9fN9at6uB/2LyFxNWr9zPWjLraPoAm"
    "SOIbRHwJoWoau5/RPdcPLfMFyHANcslMQTHn/P5PuxYreRzEUFHE8zc7kgsgrwnFCIHHwF"
    "55Jjj48IYCsrgYcV/yJ8zf7xW0RrIJKqrUHBS9wVJJcGD48HBZkMsNO667S+dA0JUWzIF0"
    "BtM0VTaEiNaJLYdlXl1TxdAjBwZPwiCjHmJNiMFisCvr6/EgGVzdXBNVcMMTeju+pMAM1m"
    "FzscSg3mi/3VdCF22ERgazRyeEVVgltpLVJUQGpLXboyJEdWoOxqbmXZzSy7yOOpyhwBH5"
    "7Wi9DV/Uq8mXh5qWWBXyQDKI/dpQCDFxT0LPPOVtJAo7pBFmhU1yYBoUpztPiZjcdsgoxz"
    "Tf5ZNe1Znlj37MQa+JAWa/sTHmXbHzPcQtt/H75m//ht2vYnlkbRtj+RahJXmWmi7dDz/O"
    "oWumBNY7F6a3o4PBf/8/Ajl1fG4SdadusPP2Jay8PP4R1++P5zKPAy03sbOWsZao7byfI7"
    "ovmpVjs5adaqJ6dnjXqz2TirxlhXVXl8270LgThVlyPm6dQvnwt0mEmfA2nbd3DKHCPqM7"
    "Moy7RXSbPs142316+vtJ6btFHxjeW/91CHdw/9XxuoFqTImmS1UKEmt4kCyqbsog6oi3rm"
    "vW/mzef6opRwKa+R1b+3fGsUgBiaHybA4+omN3Dcai1AqdNqOsEM4oyC/vVu0F9TzJWLBv"
    "Ie8wAfbGSxDxUX+exxP7HmUBRR598X61fDWjUWL2hn3ezs8s/JxR9kHCgp"
)
