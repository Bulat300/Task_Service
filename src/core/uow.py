from src.core.database import async_session_maker

class UnitOfWork:
    def __init__(self, session_factory=async_session_maker):
        self._session_factory = session_factory

    async def __aenter__(self):
        self.db = self._session_factory()
        await self.db.begin()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.db.rollback()
        else:
            await self.db.commit()
        await self.db.close()
