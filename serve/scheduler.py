"""
Cron-based schedule manager for periodic mining intelligence queries.
Stores schedules in JSON, executes queries, pushes results via 钉钉.
"""

import asyncio
import json
import hashlib
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from croniter import croniter
from loguru import logger

SCHEDULES_FILE = Path(__file__).resolve().parent.parent / "data" / "schedules.json"


def _load() -> List[Dict]:
    if SCHEDULES_FILE.exists():
        with open(SCHEDULES_FILE) as f:
            return json.load(f)
    return []


def _save(schedules: List[Dict]):
    SCHEDULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULES_FILE, "w") as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_schedules() -> List[Dict]:
    return _load()


def get_schedule(schedule_id: str) -> Optional[Dict]:
    for s in _load():
        if s["id"] == schedule_id:
            return s
    return None


def create_schedule(data: dict) -> Dict:
    schedules = _load()
    raw = f"{data['question']}:{data.get('cron','0 9 * * *')}:{_now_iso()}"
    sid = hashlib.sha256(raw.encode()).hexdigest()[:12]
    schedule = {
        "id": sid,
        "question": data["question"],
        "cron": data.get("cron", "0 9 * * *"),
        "top_k": data.get("top_k", 3),
        "source_filter": data.get("source_filter"),
        "category_filter": data.get("category_filter"),
        "enabled": data.get("enabled", True),
        "created_at": _now_iso(),
        "last_run": None,
        "last_result": None,
    }
    schedules.append(schedule)
    _save(schedules)
    return schedule


def update_schedule(schedule_id: str, data: dict) -> Optional[Dict]:
    schedules = _load()
    for i, s in enumerate(schedules):
        if s["id"] == schedule_id:
            for key in ("question", "cron", "top_k", "source_filter", "category_filter", "enabled"):
                if key in data:
                    s[key] = data[key]
            s["updated_at"] = _now_iso()
            _save(schedules)
            return s
    return None


def delete_schedule(schedule_id: str) -> bool:
    schedules = _load()
    new_list = [s for s in schedules if s["id"] != schedule_id]
    if len(new_list) < len(schedules):
        _save(new_list)
        return True
    return False


class ScheduleRunner:
    """Runs scheduled queries in a background thread."""

    def __init__(self, query_func, push_func, interval: int = 60):
        self.query_func = query_func  # async (question, top_k, source, category) -> dict
        self.push_func = push_func    # async (message: str) -> None
        self.interval = interval      # check every N seconds
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_checks: Dict[str, float] = {}

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("ScheduleRunner started (check every {}s)", self.interval)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ScheduleRunner stopped")

    def _loop(self):
        while self._running:
            try:
                self._check_all()
            except Exception as e:
                logger.error(f"ScheduleRunner error: {e}")
            time.sleep(self.interval)

    def _check_all(self):
        now = datetime.now(timezone.utc)
        schedules = _load()
        for s in schedules:
            if not s.get("enabled", True):
                continue
            try:
                cron = croniter(s["cron"], now)
                prev_run = cron.get_prev(datetime)
                prev_ts = prev_run.timestamp()

                # Only fire if we haven't already in this cycle
                last_key = s["id"]
                last_check = self._last_checks.get(last_key, 0)
                if prev_ts > last_check:
                    self._last_checks[last_key] = now.timestamp()
                    logger.info(f"Firing schedule: {s['id']} — {s['question'][:50]}")
                    self._execute(s)
            except Exception as e:
                logger.error(f"Error checking schedule {s.get('id')}: {e}")

    def _execute(self, schedule: Dict):
        """Run query and push results."""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                self.query_func(
                    schedule["question"],
                    schedule.get("top_k", 3),
                    schedule.get("source_filter"),
                    schedule.get("category_filter"),
                )
            )
            loop.close()

            # Format message
            msg = self._format_message(schedule, result)
            # Push via 钉钉
            loop2 = asyncio.new_event_loop()
            loop2.run_until_complete(self.push_func(msg))
            loop2.close()

            # Record last result
            schedules = _load()
            for s in schedules:
                if s["id"] == schedule["id"]:
                    s["last_run"] = _now_iso()
                    s["last_result"] = msg[:300]
                    break
            _save(schedules)

        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule.get('id')}: {e}")

    @staticmethod
    def _format_message(schedule: Dict, result: Dict) -> str:
        lines = [
            f"## Mining Intelligence — 定时推送",
            f"**查询:** {schedule['question']}",
            f"**时间:** {_now_iso()}",
            f"",
        ]
        if result.get("answer"):
            lines.append(f"### AI 回答")
            lines.append(result["answer"][:800])
            lines.append("")

        docs = result.get("retrieved_docs", [])
        if docs:
            lines.append(f"### 相关文档 ({len(docs)} 篇)")
            for i, doc in enumerate(docs[:5]):
                lines.append(f"{i+1}. **{doc.get('title','')}**")
                lines.append(f"   来源: {doc.get('source','')} | 评分: {doc.get('relevance_score',0)}")
                lines.append(f"   预览: {doc.get('content_preview','')[:150]}...")
                lines.append("")

        return "\n".join(lines)
