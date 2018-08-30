# -*- coding: utf-8 -*-
"""Tests for cost report API
"""
import pytest
from hansei.koku_models import KokuCostReport, KokuCustomer

# Allowed deviation between the reported total cost and the summed up daily
# costs.
DEVIATION = 1

pytest_param_all_query_param = [
    pytest.param(None, None, id='default'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'}, [['account', '*']], id='account_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'}, [['account', '*']], id='account_last_30_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'}, [['service', '*']], id='service_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'}, [['service', '*']], id='service_last_30_day'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['account', '*']], id='account_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['account', '*']], id='account_two_months_ago'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['service', '*']], id='service_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['service', '*']], id='service_two_months_ago'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['account', '*']], id='account_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['account', '*']], id='account_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['service', '*']], id='service_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['service', '*']], id='service_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'}, [['account', '*'], ['service', '*']], id='account_service_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'}, [['account', '*'], ['service', '*']], id='account_service_last_30_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'}, [['service', '*'], ['account', '*']], id='service_account_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'}, [['service', '*'], ['account', '*']], id='service_account_last_30_day'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['account', '*'], ['service', '*']], id='account_service_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['account', '*'], ['service', '*']], id='account_service_two_months_ago'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['service', '*'], ['account', '*']], id='service_account_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['service', '*'], ['account', '*']], id='service_account_two_months_ago'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['account', '*'], ['service', '*']], id='account_service_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['account', '*'], ['service', '*']], id='account_service_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'}, [['service', '*'], ['account', '*']], id='service_account_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'}, [['service', '*'], ['account', '*']], id='service_account_two_months_ago-daily'),
]

@pytest.mark.parametrize("report_filter,group_by", pytest_param_all_query_param)
def test_validate_totalcost(session_customers, report_filter, group_by):
    """
    Test to validate the total cost across daily and monthly query parameters.
    The total cost should be equal to the sum of all the daily costs
    """

    # Login as test_customer
    for customer in session_customers.values():
        report = KokuCostReport(customer.owner.client)
        report.get(report_filter=report_filter, group_by=group_by)

        # Calculate sum of daily costs
        cost_sum = report.calculate_total()

        if cost_sum is None:
            assert len(report.report_line_items()) == 0, (
                "Total cost is None but there are costs in the report")
        else:
            assert report.total['value'] - DEVIATION <= cost_sum <= \
                report.total['value'] + DEVIATION, (
                'Report total is not equal to the sum of daily costs')


@pytest.mark.parametrize("order", ['desc', 'asc'])
def test_validate_order_by(session_customers, order):
    for customer in session_customers.values():
        report = KokuCostReport(customer.owner.client)

        report.get(order_by=['cost', order], group_by=[['service', '*']])

        for group_item_list in report.report_line_items():
            prev_cost = None
            for line_item in group_item_list:
                if prev_cost is None:
                    prev_cost = line_item['total']

                # Default order is descening
                if order is None or order == 'desc':
                    assert prev_cost >= line_item['total'], 'Costs not organized in decending order'
                elif order == 'asc':
                    assert prev_cost <= line_item['total'], 'Costs not organized in ascending order'

                prev_cost = line_item['total']


