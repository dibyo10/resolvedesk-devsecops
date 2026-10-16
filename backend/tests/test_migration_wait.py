from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.wait_for_migration import wait_for_migration


def database_with_versions(versions):
    database = MagicMock()
    connection = database.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalar.side_effect = versions
    return database


def test_wait_returns_when_expected_revision_arrives():
    database = database_with_versions(["old", "current"])
    with patch("app.wait_for_migration.time.sleep") as sleep:
        wait_for_migration(database, "current", attempts=3)
    assert database.connect.call_count == 2
    sleep.assert_called_once_with(2)


def test_wait_retries_database_errors():
    database = database_with_versions(["current"])
    connection = database.connect.return_value
    database.connect.side_effect = [
        OperationalError("connect", {}, Exception()),
        connection,
    ]
    with patch("app.wait_for_migration.time.sleep"):
        wait_for_migration(database, "current", attempts=2)
    assert database.connect.call_count == 2


def test_wait_fails_when_migration_never_arrives():
    database = database_with_versions(["old", "old"])
    with patch("app.wait_for_migration.time.sleep") as sleep:
        with pytest.raises(RuntimeError, match="migration did not become ready"):
            wait_for_migration(database, "current", attempts=2)
    sleep.assert_called_once_with(2)
