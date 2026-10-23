"""Dependencies shared by the controllers."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    """Provide a database session scoped to the current request.

    Args:
        request: Incoming request, used to reach the application state.

    Yields:
        An open session, closed once the response is sent.
    """
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
