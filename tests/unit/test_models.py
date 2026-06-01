"""Unit tests for lampyrid models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from lampyrid.models.firefly_models import TransactionTypeProperty
from lampyrid.models.lampyrid_models import (
    CreateAccountRequest,
    CreateBudgetRequest,
    CreateBulkTransactionsRequest,
    CreateDepositRequest,
    CreateWithdrawalRequest,
    SearchTransactionsRequest,
    Transaction,
    UpdateAccountRequest,
    utc_now,
)


@pytest.mark.unit
class TestLampyridModels:
    """Test cases for lampyrid models."""

    def test_utc_now(self):
        """Test utc_now function returns a datetime with UTC timezone."""
        result = utc_now()

        # Should return a datetime object
        assert hasattr(result, 'year')
        assert hasattr(result, 'month')
        assert hasattr(result, 'day')
        assert hasattr(result, 'hour')
        assert hasattr(result, 'minute')
        assert hasattr(result, 'second')

    def test_search_transactions_request_with_no_criteria(self):
        """Test SearchTransactionsRequest validation with no search criteria."""
        with pytest.raises(ValueError, match='At least one search criterion must be provided'):
            SearchTransactionsRequest(
                # No search fields provided
            )

    def test_search_transactions_request_with_empty_criteria(self):
        """Test SearchTransactionsRequest validation with empty string criteria."""
        with pytest.raises(ValueError, match='At least one search criterion must be provided'):
            SearchTransactionsRequest(
                query='',  # Empty string
            )

    def test_search_transactions_request_with_valid_criteria(self):
        """Test SearchTransactionsRequest validation passes with valid criteria."""
        # Should not raise any exception
        request = SearchTransactionsRequest(query='valid query')

        assert request.query == 'valid query'


@pytest.mark.unit
class TestCreateWithdrawalRequest:
    """Test cases for CreateWithdrawalRequest model."""

    def test_create_withdrawal_request_allows_destination_id(self):
        """Test that CreateWithdrawalRequest accepts destination_id field."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
            destination_id='5',
        )

        assert request.destination_id == '5'
        assert request.destination_name is None

    def test_create_withdrawal_request_allows_destination_name(self):
        """Test that CreateWithdrawalRequest accepts destination_name field."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
            destination_name='Groceries',
        )

        assert request.destination_name == 'Groceries'
        assert request.destination_id is None

    def test_create_withdrawal_request_allows_neither_destination(self):
        """Test that destination_id and destination_name may be omitted."""
        request = CreateWithdrawalRequest(
            amount=25.50,
            description='Test withdrawal',
            source_id='1',
        )

        assert request.destination_id is None
        assert request.destination_name is None


@pytest.mark.unit
class TestCreateDepositRequest:
    """Test cases for CreateDepositRequest model."""

    def test_create_deposit_request_allows_source_id(self):
        """Test that CreateDepositRequest accepts source_id field."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
            source_id='7',
        )

        assert request.source_id == '7'
        assert request.source_name is None

    def test_create_deposit_request_allows_source_name(self):
        """Test that CreateDepositRequest accepts source_name field."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
            source_name='Employer',
        )

        assert request.source_name == 'Employer'
        assert request.source_id is None

    def test_create_deposit_request_allows_neither_source(self):
        """Test that CreateDepositRequest allows neither source_id nor source_name."""
        request = CreateDepositRequest(
            amount=500.00,
            description='Test deposit',
            destination_id='1',
        )

        assert request.source_id is None
        assert request.source_name is None

    def test_create_deposit_request_mutual_exclusivity(self):
        """Test that source_id and source_name cannot both be provided."""
        with pytest.raises(ValidationError) as exc_info:
            CreateDepositRequest(
                amount=500.00,
                description='Test deposit',
                destination_id='1',
                source_id='7',
                source_name='Employer',
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert 'Cannot specify both source_id and source_name' in str(errors[0]['msg'])


@pytest.mark.unit
class TestCreateBulkTransactionsRequest:
    """Test cases for CreateBulkTransactionsRequest model."""

    def test_create_bulk_transactions_request_atomic_default(self):
        """Test CreateBulkTransactionsRequest with default atomic value."""
        transaction = Transaction(
            type=TransactionTypeProperty.withdrawal,
            amount=25.50,
            description='Test withdrawal',
            date=utc_now(),
            source_id='1',
            destination_id='2',
        )

        request = CreateBulkTransactionsRequest(transactions=[transaction])

        assert len(request.transactions) == 1
        assert request.atomic is True  # Default value


@pytest.mark.unit
class TestCreateBudgetRequest:
    """Test cases for CreateBudgetRequest model."""

    def test_create_budget_request_valid_no_auto(self):
        """Test valid budget request without auto-budget."""
        request = CreateBudgetRequest(name='Groceries')
        assert request.name == 'Groceries'
        assert request.auto_budget_type is None

    def test_create_budget_request_valid_with_auto(self):
        """Test valid budget request with auto-budget."""
        request = CreateBudgetRequest(
            name='Groceries',
            auto_budget_type='reset',
            auto_budget_amount=100.0,
            auto_budget_period='monthly',
        )
        assert request.auto_budget_type == 'reset'
        assert request.auto_budget_amount == 100.0
        assert request.auto_budget_period == 'monthly'

    def test_create_budget_request_missing_amount(self):
        """Test budget request with type but missing amount."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBudgetRequest(
                name='Groceries',
                auto_budget_type='reset',
                auto_budget_period='monthly',
            )
        assert 'auto_budget_amount is required when auto_budget_type is set' in str(exc_info.value)

    def test_create_budget_request_missing_period(self):
        """Test budget request with type but missing period."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBudgetRequest(
                name='Groceries',
                auto_budget_type='rollover',
                auto_budget_amount=100.0,
            )
        assert 'auto_budget_period is required when auto_budget_type is set' in str(exc_info.value)

    def test_create_budget_request_none_type(self):
        """Test budget request with auto_budget_type='none'."""
        request = CreateBudgetRequest(name='Groceries', auto_budget_type='none')
        assert request.auto_budget_type == 'none'
        assert request.auto_budget_amount is None
        assert request.auto_budget_period is None


@pytest.mark.unit
class TestUpdateAccountRequest:
    """Test cases for UpdateAccountRequest model."""

    def test_update_account_request_minimum_only_account_id(self):
        """account_id alone is sufficient — every other field is optional."""
        request = UpdateAccountRequest(account_id='852')
        assert request.account_id == '852'
        # All other fields default to None
        assert request.name is None
        assert request.opening_balance is None
        assert request.opening_balance_date is None
        assert request.notes is None

    def test_update_account_request_opening_balance_set(self):
        """opening_balance + opening_balance_date round-trip correctly."""
        when = datetime(2021, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        request = UpdateAccountRequest(
            account_id='852',
            opening_balance=-977500.0,
            opening_balance_date=when,
        )
        # exclude_unset should drop everything except what we explicitly set
        dumped = request.model_dump(exclude_unset=True)
        assert dumped == {
            'account_id': '852',
            'opening_balance': -977500.0,
            'opening_balance_date': when,
        }

    def test_update_account_request_rejects_extra_fields(self):
        """Extra fields not in the schema must be rejected (extra='forbid')."""
        with pytest.raises(ValidationError, match='Extra inputs are not permitted'):
            UpdateAccountRequest(account_id='852', unknown_field='nope')  # type: ignore[call-arg]

    def test_update_account_request_requires_account_id(self):
        """account_id is the only required field."""
        with pytest.raises(ValidationError, match='account_id'):
            UpdateAccountRequest()  # type: ignore[call-arg]


@pytest.mark.unit
class TestCreateAccountRequest:
    """Test cases for CreateAccountRequest model."""

    def test_create_account_request_minimum_required(self):
        """Name + type are the only required fields."""
        request = CreateAccountRequest(name='New asset', type='asset')
        assert request.name == 'New asset'
        assert request.type == 'asset'
        # Optional fields default to None / True per field defaults
        assert request.opening_balance is None
        assert request.notes is None
        # active default is True per Firefly's AccountStore convention
        assert request.active is True
        assert request.include_net_worth is True

    def test_create_account_request_with_opening_balance(self):
        """opening_balance + opening_balance_date are usable together."""
        when = datetime(2021, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        request = CreateAccountRequest(
            name='Mortgage',
            type='asset',
            opening_balance=-977500.0,
            opening_balance_date=when,
            currency_code='SEK',
        )
        assert request.opening_balance == -977500.0
        assert request.opening_balance_date == when
        assert request.currency_code == 'SEK'

    def test_create_account_request_rejects_extra_fields(self):
        """Extra fields not in the schema must be rejected (extra='forbid')."""
        with pytest.raises(ValidationError, match='Extra inputs are not permitted'):
            CreateAccountRequest(name='X', type='asset', unknown='nope')  # type: ignore[call-arg]

    def test_create_account_request_requires_name_and_type(self):
        """Name and type are required."""
        with pytest.raises(ValidationError):
            CreateAccountRequest(name='X')  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            CreateAccountRequest(type='asset')  # type: ignore[call-arg]
