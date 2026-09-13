"""Celery 异步任务：批量发通知等耗时操作。"""
import logging

from celery import Celery

logger = logging.getLogger(__name__)

celery = Celery(
    "campus_system",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0",
)


@celery.task
def batch_publish_notice(title, content, publisher, publisher_role, targets):
    """批量发布通知到多个目标（异步）。

    targets: 目标列表，如 ["全校", "软件2401", "1号楼"]
    """
    from campus_system.db import db
    from campus_system.models import Notice

    published = []
    for scope in targets:
        notice = Notice(
            title=title,
            content=content,
            publisher=publisher,
            publisher_role=publisher_role,
            scope=scope,
            category="学校",
            pinned=False,
            status="已发布",
        )
        db.session.add(notice)
        published.append(scope)
    db.session.commit()
    logger.info("批量发布通知完成: %s -> %s", title, published)
    return {"title": title, "published_to": published, "count": len(published)}
