"""Unit tests for TransactionService.update_transaction payload building."""

from unittest.mock import AsyncMock, patch

import pytest

from lampyrid.models.lampyrid_models import UpdateTransactionRequest
from lampyrid.services.transactions import TransactionService


@pytest.fixture
def service():
    client = AsyncMock()
    client.update_transaction = AsyncMock(return_value=object())
    return TransactionService(client), client


def _sent_split(client):
    _, transaction_update = client.update_transaction.call_args.args
    return transaction_update.transactions[0]


@pytest.mark.asyncio
async def test_update_transaction_passes_currency_code(service):
    svc, client = service
    req = UpdateTransactionRequest(
        transaction_id='4519',
        amount=1888.45,
        currency_code='SEK',
        foreign_amount=140.0,
        foreign_currency_code='GBP',
    )
    with patch('lampyrid.services.transactions.Transaction.from_transaction_single'):
        await svc.update_transaction(req)
    split = _sent_split(client)
    assert split.currency_code == 'SEK'
    assert split.amount == '1888.45'
    assert split.foreign_amount == '140.0'
    assert split.foreign_currency_code == 'GBP'


@pytest.mark.asyncio
async def test_update_transaction_omits_currency_code_when_not_given(service):
    svc, client = service
    req = UpdateTransactionRequest(transaction_id='1', category_name='Groceries')
    with patch('lampyrid.services.transactions.Transaction.from_transaction_single'):
        await svc.update_transaction(req)
    split = _sent_split(client)
    assert split.currency_code is None
    assert 'currency_code' not in split.model_dump(exclude_none=True)
