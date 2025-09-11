from pathlib import Path
from typing import Generator
import os

from sqlmodel import SQLModel, create_engine, Session

# Determine database URL from env or default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
	DB_DIR = Path("data")
	DB_DIR.mkdir(parents=True, exist_ok=True)
	DB_PATH = DB_DIR / "trades.db"
	DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
	CONNECT_ARGS = {"check_same_thread": False}
else:
	# For Postgres on Render/Cloud, allow both postgres:// and postgresql://
	if DATABASE_URL.startswith("postgres://"):
		DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
	CONNECT_ARGS = {}

engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)


def init_db() -> None:
	SQLModel.metadata.create_all(engine)
	_run_migrations()


def _run_migrations() -> None:
	# lightweight migrations for SQLite/Postgres
	with engine.connect() as conn:
		# spottrade.fee_currency
		try:
			res = conn.exec_driver_sql("PRAGMA table_info('spottrade')")
			cols = {row[1] for row in res.fetchall()}
			if "fee_currency" not in cols:
				conn.exec_driver_sql(
					"ALTER TABLE spottrade ADD COLUMN fee_currency VARCHAR DEFAULT 'quote'"
				)
		except Exception:
			try:
				res = conn.exec_driver_sql(
					"""
						SELECT column_name FROM information_schema.columns
						WHERE table_name = 'spottrade'
					"""
				)
				cols = {r[0] for r in res.fetchall()}
				if "fee_currency" not in cols:
					conn.exec_driver_sql(
						"ALTER TABLE spottrade ADD COLUMN fee_currency VARCHAR DEFAULT 'quote'"
					)
			except Exception:
				pass

		# contractbot.bot_name
		try:
			res = conn.exec_driver_sql("PRAGMA table_info('contractbot')")
			cols = {row[1] for row in res.fetchall()}
			if "bot_name" not in cols:
				conn.exec_driver_sql(
					"ALTER TABLE contractbot ADD COLUMN bot_name VARCHAR"
				)
		except Exception:
			try:
				res = conn.exec_driver_sql(
					"""
						SELECT column_name FROM information_schema.columns
						WHERE table_name = 'contractbot'
					"""
				)
				cols = {r[0] for r in res.fetchall()}
				if "bot_name" not in cols:
					conn.exec_driver_sql(
						"ALTER TABLE contractbot ADD COLUMN bot_name VARCHAR"
					)
			except Exception:
				pass

		# ensure investmentpair table exists by attempting a simple select
		try:
			conn.exec_driver_sql("SELECT 1 FROM investmentpair LIMIT 1")
		except Exception:
			# create table via metadata
			SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
	with Session(engine) as session:
		yield session
