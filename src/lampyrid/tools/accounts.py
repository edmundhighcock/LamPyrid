"""Account Management MCP Tools.

This module provides MCP tools for managing Firefly III accounts including
listing, searching, retrieving, creating, and updating accounts.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import (
    Account,
    CreateAccountRequest,
    GetAccountRequest,
    ListAccountRequest,
    SearchAccountRequest,
    UpdateAccountRequest,
)
from ..services.accounts import AccountService


def create_accounts_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for account management tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with account management tools registered

    """
    account_service = AccountService(client)

    accounts_mcp = FastMCP('accounts')

    @accounts_mcp.tool(tags={'accounts'})
    async def list_accounts(req: ListAccountRequest) -> List[Account]:
        """Retrieve accounts from Firefly III.

        Use 'asset' for checking/savings accounts, 'expense' for spending accounts, 'revenue' for
        income sources. Essential for finding account IDs before creating transactions.
        """
        return await account_service.list_accounts(req)

    @accounts_mcp.tool(tags={'accounts'})
    async def get_account(req: GetAccountRequest) -> Account:
        """Retrieve detailed account information including current balance and currency.

        Use this to verify account details before transactions.
        """
        return await account_service.get_account(req)

    @accounts_mcp.tool(tags={'accounts'})
    async def search_accounts(req: SearchAccountRequest) -> List[Account]:
        """Find accounts by partial name matching.

        Useful when you know the account name but not the ID. Supports filtering by account type.
        """
        return await account_service.search_accounts(req)

    @accounts_mcp.tool(tags={'accounts', 'manage'})
    async def create_account(req: CreateAccountRequest) -> Account:
        """Create a new account in Firefly III.

        Use for adding a new bank account, a loan modelled as an asset account, an
        expense category, or a revenue source. Set opening_balance + opening_balance_date
        if the account starts with a non-zero balance (e.g. a mortgage with an origination
        principal that pre-dates Firefly).
        """
        return await account_service.create_account_from_request(req)

    @accounts_mcp.tool(tags={'accounts', 'manage'})
    async def update_account(req: UpdateAccountRequest) -> Account:
        """Modify fields on an existing account.

        Primary use: setting opening_balance + opening_balance_date on a loan whose
        opening principal was never journalled into Firefly. Also useful for updating
        account notes, IBAN, interest rate, or toggling active. Only fields you set
        are sent — omitted fields are left unchanged.
        """
        return await account_service.update_account(req)

    return accounts_mcp
