"""Unit tests for rule-group operations on RuleService."""

from unittest.mock import AsyncMock

import pytest

from lampyrid.models.firefly_models import (
    Meta,
    ObjectLink,
    PageLink,
    Pagination,
    RuleGroup,
    RuleGroupArray,
    RuleGroupRead,
    RuleGroupSingle,
)
from lampyrid.models.lampyrid_models import (
    CreateRuleGroupRequest,
    ListRuleGroupsRequest,
    UpdateRuleGroupRequest,
)
from lampyrid.services.rules import RuleService


def _make_group_read(
    group_id: str = '1',
    title: str = 'Default rule group',
    order: int | None = 1,
    active: bool = True,
    description: str | None = None,
) -> RuleGroupRead:
    """Create RuleGroupRead for testing."""
    return RuleGroupRead(
        type='rules_group',
        id=group_id,
        attributes=RuleGroup(
            title=title,
            description=description,
            order=order,
            active=active,
        ),
        links=ObjectLink(self='http://example.com'),
    )


def _make_group_array(
    groups: list[RuleGroupRead], current_page: int = 1, total_pages: int = 1
) -> RuleGroupArray:
    """Create RuleGroupArray with pagination."""
    return RuleGroupArray(
        data=groups,
        meta=Meta(
            pagination=Pagination(
                total=len(groups),
                count=len(groups),
                per_page=50,
                current_page=current_page,
                total_pages=total_pages,
            )
        ),
        links=PageLink(
            self='http://example.com',
            first='http://example.com?page=1',
            last=f'http://example.com?page={total_pages}',
        ),
    )


class TestRuleGroupService:
    """Test cases for rule-group methods on RuleService."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock FireflyClient."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_client):
        """Create a RuleService with mocked client."""
        return RuleService(mock_client)

    @pytest.mark.asyncio
    async def test_list_rule_groups_sorted_by_order(self, service, mock_client):
        """Groups come back sorted ascending by processing order."""
        g_last = _make_group_read(group_id='3', title='Budgets', order=3)
        g_first = _make_group_read(group_id='1', title='Default', order=1)
        g_mid = _make_group_read(group_id='2', title='Classifications', order=2)
        mock_client.get_rule_groups.return_value = _make_group_array([g_last, g_first, g_mid])

        groups = await service.list_rule_groups(ListRuleGroupsRequest())

        assert [g.id for g in groups] == ['1', '2', '3']
        assert groups[-1].title == 'Budgets'
        mock_client.get_rule_groups.assert_awaited_once_with(page=1)

    @pytest.mark.asyncio
    async def test_list_rule_groups_paginates(self, service, mock_client):
        """All pages are fetched."""
        page1 = _make_group_array(
            [_make_group_read(group_id='1', order=1)], current_page=1, total_pages=2
        )
        page2 = _make_group_array(
            [_make_group_read(group_id='2', order=2)], current_page=2, total_pages=2
        )
        mock_client.get_rule_groups.side_effect = [page1, page2]

        groups = await service.list_rule_groups(ListRuleGroupsRequest())

        assert len(groups) == 2
        assert mock_client.get_rule_groups.await_count == 2

    @pytest.mark.asyncio
    async def test_list_rule_groups_none_order_sorts_last(self, service, mock_client):
        """Groups without an order sort after ordered groups."""
        g_none = _make_group_read(group_id='9', title='No order', order=None)
        g_one = _make_group_read(group_id='1', title='First', order=1)
        mock_client.get_rule_groups.return_value = _make_group_array([g_none, g_one])

        groups = await service.list_rule_groups(ListRuleGroupsRequest())

        assert [g.id for g in groups] == ['1', '9']

    @pytest.mark.asyncio
    async def test_create_rule_group(self, service, mock_client):
        """Create passes through title/description/active and returns the group."""
        created = _make_group_read(group_id='4', title='Budgets', order=4)
        mock_client.create_rule_group.return_value = RuleGroupSingle(data=created)

        group = await service.create_rule_group(
            CreateRuleGroupRequest(title='Budgets', description='Runs last')
        )

        assert group.id == '4'
        assert group.title == 'Budgets'
        store = mock_client.create_rule_group.await_args.args[0]
        assert store.title == 'Budgets'
        assert store.description == 'Runs last'
        assert store.active is True

    @pytest.mark.asyncio
    async def test_update_rule_group_only_sends_set_fields(self, service, mock_client):
        """Update builds RuleGroupUpdate with only the provided fields."""
        updated = _make_group_read(group_id='4', title='Budgets', order=9)
        mock_client.update_rule_group.return_value = RuleGroupSingle(data=updated)

        group = await service.update_rule_group(UpdateRuleGroupRequest(rule_group_id='4', order=9))

        assert group.order == 9
        args = mock_client.update_rule_group.await_args.args
        assert args[0] == '4'
        update = args[1]
        assert update.order == 9
        assert update.model_fields_set == {'order'}
