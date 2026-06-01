"""Account Service for LamPyrid.

This service handles account-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

from typing import List

from ..clients.firefly import FireflyClient
from ..models.firefly_models import (
    AccountRoleProperty,
    AccountRolePropertyEnum,
    AccountStore,
    AccountUpdate,
    InterestPeriodProperty,
    InterestPeriodPropertyEnum,
    LiabilityDirectionProperty,
    LiabilityDirectionPropertyEnum,
    LiabilityTypeProperty,
    LiabilityTypePropertyEnum,
    ShortAccountTypeProperty,
)
from ..models.lampyrid_models import (
    Account,
    CreateAccountRequest,
    GetAccountRequest,
    ListAccountRequest,
    SearchAccountRequest,
    UpdateAccountRequest,
)


class AccountService:
    """Service for managing Firefly III accounts.

    This service provides a high-level interface for account operations,
    handling model conversion and business logic while delegating
    HTTP operations to the FireflyClient.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the account service with a FireflyClient instance."""
        self._client = client

    async def list_accounts(self, req: ListAccountRequest) -> List[Account]:
        """List accounts with optional type filtering.

        Args:
                req: Request containing account type filter

        Returns:
                List of accounts matching the filter criteria

        """
        account_array = await self._client.list_accounts(type=req.type)

        return [Account.from_account_read(account_read) for account_read in account_array.data]

    async def get_account(self, req: GetAccountRequest) -> Account:
        """Get detailed information for a single account.

        Args:
                req: Request containing the account ID

        Returns:
                Account details including balance and metadata

        """
        account_single = await self._client.get_account(req.id)
        return Account.from_account_read(account_single.data)

    async def search_accounts(self, req: SearchAccountRequest) -> List[Account]:
        """Search accounts by name with optional type filtering.

        Args:
                req: Request containing search query and type filter

        Returns:
                List of accounts matching the search criteria

        """
        account_array = await self._client.search_accounts(req.query, req.type)

        return [Account.from_account_read(account_read) for account_read in account_array.data]

    async def create_account(self, account_store: AccountStore) -> Account:
        """Create a new account from a fully-populated Firefly AccountStore.

        This is the lower-level entry point used by tests and internal callers that
        already hold a Firefly AccountStore. MCP callers should use
        `create_account_from_request` instead.

        Args:
                account_store: Account data for creation

        Returns:
                Created account details

        """
        account_single = await self._client.create_account(account_store)
        return Account.from_account_read(account_single.data)

    async def create_account_from_request(self, req: CreateAccountRequest) -> Account:
        """Create a new account from a LamPyrid CreateAccountRequest.

        Builds a Firefly AccountStore from the LamPyrid-shaped request and delegates
        to `create_account`. Used by the MCP tool.

        Args:
                req: LamPyrid request shape (more LLM-friendly types than AccountStore).

        Returns:
                Created account details.

        """
        store_kwargs: dict = {
            'name': req.name,
            'type': ShortAccountTypeProperty(req.type),
        }
        if req.iban is not None:
            store_kwargs['iban'] = req.iban
        if req.bic is not None:
            store_kwargs['bic'] = req.bic
        if req.account_number is not None:
            store_kwargs['account_number'] = req.account_number
        if req.opening_balance is not None:
            store_kwargs['opening_balance'] = str(req.opening_balance)
        if req.opening_balance_date is not None:
            store_kwargs['opening_balance_date'] = req.opening_balance_date
        if req.virtual_balance is not None:
            store_kwargs['virtual_balance'] = str(req.virtual_balance)
        if req.currency_code is not None:
            store_kwargs['currency_code'] = req.currency_code
        if req.currency_id is not None:
            store_kwargs['currency_id'] = req.currency_id
        if req.active is not None:
            store_kwargs['active'] = req.active
        if req.include_net_worth is not None:
            store_kwargs['include_net_worth'] = req.include_net_worth
        if req.account_role is not None:
            store_kwargs['account_role'] = AccountRoleProperty(
                AccountRolePropertyEnum(req.account_role)
            )
        if req.liability_type is not None:
            store_kwargs['liability_type'] = LiabilityTypeProperty(
                LiabilityTypePropertyEnum(req.liability_type)
            )
        if req.liability_direction is not None:
            store_kwargs['liability_direction'] = LiabilityDirectionProperty(
                LiabilityDirectionPropertyEnum(req.liability_direction)
            )
        if req.interest is not None:
            store_kwargs['interest'] = req.interest
        if req.interest_period is not None:
            store_kwargs['interest_period'] = InterestPeriodProperty(
                InterestPeriodPropertyEnum(req.interest_period)
            )
        if req.notes is not None:
            store_kwargs['notes'] = req.notes

        return await self.create_account(AccountStore(**store_kwargs))

    async def update_account(self, req: UpdateAccountRequest) -> Account:
        """Update an existing account.

        Firefly's AccountUpdate model requires `name`; if the caller omits it, we
        fetch the existing account to pre-populate it. Other fields are only sent
        when explicitly provided by the caller (partial update via exclude_unset).

        Args:
                req: Request containing updated account fields.

        Returns:
                Updated account details.

        """
        # Firefly's PUT /accounts/{id} requires the name field even on partial updates,
        # so fetch the current name if the caller didn't supply one.
        if req.name is None:
            current = await self._client.get_account(req.account_id)
            existing_name = current.data.attributes.name
        else:
            existing_name = req.name

        update_kwargs: dict = {'name': existing_name}

        if req.iban is not None:
            update_kwargs['iban'] = req.iban
        if req.bic is not None:
            update_kwargs['bic'] = req.bic
        if req.account_number is not None:
            update_kwargs['account_number'] = req.account_number
        if req.opening_balance is not None:
            update_kwargs['opening_balance'] = str(req.opening_balance)
        if req.opening_balance_date is not None:
            update_kwargs['opening_balance_date'] = req.opening_balance_date
        if req.virtual_balance is not None:
            update_kwargs['virtual_balance'] = str(req.virtual_balance)
        if req.currency_code is not None:
            update_kwargs['currency_code'] = req.currency_code
        if req.currency_id is not None:
            update_kwargs['currency_id'] = req.currency_id
        if req.active is not None:
            update_kwargs['active'] = req.active
        if req.include_net_worth is not None:
            update_kwargs['include_net_worth'] = req.include_net_worth
        if req.account_role is not None:
            update_kwargs['account_role'] = AccountRoleProperty(
                AccountRolePropertyEnum(req.account_role)
            )
        if req.liability_type is not None:
            update_kwargs['liability_type'] = LiabilityTypeProperty(
                LiabilityTypePropertyEnum(req.liability_type)
            )
        if req.interest is not None:
            update_kwargs['interest'] = req.interest
        if req.interest_period is not None:
            update_kwargs['interest_period'] = InterestPeriodProperty(
                InterestPeriodPropertyEnum(req.interest_period)
            )
        if req.notes is not None:
            update_kwargs['notes'] = req.notes

        account_update = AccountUpdate(**update_kwargs)
        account_single = await self._client.update_account(req.account_id, account_update)
        return Account.from_account_read(account_single.data)
