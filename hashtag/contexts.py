from contextlib import contextmanager


@contextmanager
def session_scope(sbuilder):
    """Provide a transactional scope around a series of operations."""
    session = sbuilder()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

