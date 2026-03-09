from .db.mongo_client import init_db, close_db
from .models.headline import Headline
from .models.summary import Summary

__all__ = ["init_db", "close_db", "Headline", "Summary"]