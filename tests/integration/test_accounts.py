"""Integration tests for account management tools."""

from datetime import datetime, timezone

import pytest
from dirty_equals import IsFloat
from fastmcp import Client
from fastmcp.exceptions import ToolError
from inline_snapshot import snapshot

from lampyrid.models.lampyrid_models import Account


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_all(mcp_client):
    """Test listing all account types."""
    result = await mcp_client.call_tool('list_accounts', {'req': {'type': 'all'}})
    accounts = result.structured_content['result']

    # Should have at least one account
    assert len(accounts) > 0

    # All accounts should have required fields
    for account in accounts:
        assert account['id'] is not None
        assert account['name'] is not None
        assert account['type'] is not None

    # Validate account structure with snapshot
    assert accounts == snapshot(
        [
            {
                'id': '2',
                'name': 'Initial balance for "Test Checking"',
                'type': 'initial-balance',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
            {
                'id': '4',
                'name': 'Initial balance for "Test Savings"',
                'type': 'initial-balance',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
            {
                'id': '5',
                'name': 'Test Expense',
                'type': 'expense',
                'currency_code': 'EUR',
                'current_balance': IsFloat(),
            },
            {
                'id': '6',
                'name': 'Test Expense 2',
                'type': 'expense',
                'currency_code': 'EUR',
                'current_balance': 0.0,
            },
            {
                'id': '7',
                'name': 'Test Revenue',
                'type': 'revenue',
                'currency_code': 'EUR',
                'current_balance': IsFloat(),
            },
            {
                'id': '1',
                'name': 'Test Checking',
                'type': 'asset',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
            {
                'id': '3',
                'name': 'Test Savings',
                'type': 'asset',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
        ]
    )


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_asset(mcp_client):
    """Test filtering accounts by asset type."""
    result = await mcp_client.call_tool('list_accounts', {'req': {'type': 'asset'}})
    accounts = result.structured_content['result']

    # Should have at least one asset account for tests to work
    assert len(accounts) > 0

    # All accounts should be asset type
    for account in accounts:
        assert account['type'] == 'asset'

    assert accounts == snapshot(
        [
            {
                'id': '1',
                'name': 'Test Checking',
                'type': 'asset',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
            {
                'id': '3',
                'name': 'Test Savings',
                'type': 'asset',
                'currency_code': 'USD',
                'current_balance': IsFloat(),
            },
        ]
    )


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_expense(mcp_client):
    """Test filtering accounts by expense type."""
    result = await mcp_client.call_tool('list_accounts', {'req': {'type': 'expense'}})
    accounts = result.structured_content['result']

    # May or may not have expense accounts
    # If we have any, they should all be expense type
    for account in accounts:
        assert account['type'] == 'expense'

    assert accounts == snapshot(
        [
            {
                'id': '5',
                'name': 'Test Expense',
                'type': 'expense',
                'currency_code': 'EUR',
                'current_balance': IsFloat(),
            },
            {
                'id': '6',
                'name': 'Test Expense 2',
                'type': 'expense',
                'currency_code': 'EUR',
                'current_balance': 0.0,
            },
        ]
    )


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_list_accounts_by_type_revenue(mcp_client: Client):
    """Test filtering accounts by revenue type."""
    result = await mcp_client.call_tool('list_accounts', {'req': {'type': 'revenue'}})
    assert result.structured_content is not None
    accounts = result.structured_content['result']

    assert len(accounts) > 0
    assert accounts == snapshot(
        [
            {
                'id': '7',
                'name': 'Test Revenue',
                'type': 'revenue',
                'currency_code': 'EUR',
                'current_balance': IsFloat(),
            }
        ]
    )


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_get_account_valid(mcp_client: Client, test_asset_account: Account):
    """Test retrieving a single account by valid ID."""
    result = await mcp_client.call_tool('get_account', {'req': {'id': test_asset_account.id}})
    account = Account.model_validate(result.structured_content)

    # Should return the same account
    assert account.id == test_asset_account.id
    assert account.name == test_asset_account.name
    assert account.type.value == test_asset_account.type.value

    # Validate account structure with snapshot
    assert result.structured_content == snapshot(
        {
            'id': '1',
            'name': 'Test Checking',
            'type': 'asset',
            'currency_code': 'USD',
            'current_balance': IsFloat(),
        }
    )


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_get_account_invalid(mcp_client):
    """Test handling of invalid account ID (404)."""
    # FastMCP Client wraps HTTPStatusError in ToolError
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool('get_account', {'req': {'id': '999999'}})

    assert '404' in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_exact(mcp_client, test_asset_account: Account):
    """Test searching accounts with exact name match."""
    result = await mcp_client.call_tool(
        'search_accounts', {'req': {'query': test_asset_account.name}}
    )
    accounts = result.structured_content['result']

    # Should find at least the test account
    assert len(accounts) > 0

    # Should contain our test account
    account_ids = [account['id'] for account in accounts]
    assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_partial(mcp_client, test_asset_account: Account):
    """Test searching accounts with partial name matching."""
    # Use first 3 characters of account name
    partial_name = test_asset_account.name[:3]
    result = await mcp_client.call_tool('search_accounts', {'req': {'query': partial_name}})
    accounts = result.structured_content['result']

    # Should find at least one account
    assert len(accounts) > 0

    # Should contain our test account (or at least accounts starting with the partial name)
    account_ids = [account['id'] for account in accounts]
    assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_with_type(mcp_client, test_asset_account: Account):
    """Test searching accounts with type filtering."""
    result = await mcp_client.call_tool(
        'search_accounts', {'req': {'query': test_asset_account.name, 'type': 'asset'}}
    )
    accounts = result.structured_content['result']

    # Should find at least the test account
    assert len(accounts) > 0

    # All results should be asset type
    for account in accounts:
        assert account['type'] == 'asset'

    # Should contain our test account
    account_ids = [account['id'] for account in accounts]
    assert test_asset_account.id in account_ids


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_search_accounts_no_results(mcp_client):
    """Test searching accounts with no matching results."""
    # Use a query that should not match any account
    result = await mcp_client.call_tool(
        'search_accounts', {'req': {'query': 'xyzabc123nonexistent'}}
    )
    accounts = result.structured_content['result']

    # Should return empty list
    assert len(accounts) == 0


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_create_account_minimal(mcp_client: Client, firefly_client):
    """Test create_account with the minimum required fields."""
    name = 'pytest-create-account-minimal'
    try:
        result = await mcp_client.call_tool(
            'create_account',
            {'req': {'name': name, 'type': 'expense'}},
        )
        created = Account.model_validate(result.structured_content)
        assert created.name == name
        assert created.type.value == 'expense'
        assert created.id is not None
    finally:
        # Cleanup: best-effort delete; not all Firefly setups expose account delete via MCP,
        # so this leaves the test account behind if cleanup isn't available. Mark in name.
        pass


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_create_account_with_opening_balance(mcp_client: Client):
    """Test create_account propagates opening_balance + opening_balance_date."""
    name = 'pytest-create-account-with-opening'
    opening_date = datetime(2021, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
    result = await mcp_client.call_tool(
        'create_account',
        {
            'req': {
                'name': name,
                'type': 'asset',
                'opening_balance': -100000.00,
                'opening_balance_date': opening_date.isoformat(),
                'currency_code': 'SEK',
                'account_role': 'defaultAsset',
            }
        },
    )
    created = Account.model_validate(result.structured_content)
    assert created.name == name
    assert created.type.value == 'asset'
    # Current balance should equal the opening balance immediately after creation
    assert created.current_balance == -100000.00


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_update_account_notes(mcp_client: Client, test_asset_account: Account):
    """Test update_account modifies notes while leaving other fields intact."""
    new_notes = 'pytest-update-notes marker'
    result = await mcp_client.call_tool(
        'update_account',
        {'req': {'account_id': test_asset_account.id, 'notes': new_notes}},
    )
    updated = Account.model_validate(result.structured_content)
    # Name should be preserved automatically (we didn't supply it)
    assert updated.name == test_asset_account.name
    assert updated.id == test_asset_account.id
    assert updated.type.value == test_asset_account.type.value


@pytest.mark.asyncio
@pytest.mark.accounts
@pytest.mark.integration
async def test_update_account_opening_balance(mcp_client: Client):
    """Test update_account can set opening_balance + opening_balance_date.

    Creates an asset account first (no opening balance), then sets one via update_account
    and confirms the current_balance moves to match.
    """
    # Create a fresh account with no opening balance
    name = 'pytest-update-opening-balance'
    create_result = await mcp_client.call_tool(
        'create_account',
        {'req': {'name': name, 'type': 'asset', 'currency_code': 'SEK'}},
    )
    created = Account.model_validate(create_result.structured_content)
    assert created.current_balance == 0.0

    # Set an opening balance via update_account
    opening_date = datetime(2021, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
    update_result = await mcp_client.call_tool(
        'update_account',
        {
            'req': {
                'account_id': created.id,
                'opening_balance': -977500.00,
                'opening_balance_date': opening_date.isoformat(),
            }
        },
    )
    updated = Account.model_validate(update_result.structured_content)
    assert updated.id == created.id
    assert updated.name == name  # name preserved automatically
    # Balance should reflect the new opening balance
    assert updated.current_balance == -977500.00
