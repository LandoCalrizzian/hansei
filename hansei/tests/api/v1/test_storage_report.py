# -*- coding: utf-8 -*-
"""Tests for storage inventory report API

The tests assume that the database is pre-populated with data including the
Koku default 'test_customer' customer by running 'make oc-create-test-db-file'.
"""
import pytest
from hansei.koku_models import KokuStorageReport, KokuCustomer

# Allowed deviation between the reported total storage usage and the summed up
# storage usage from the individual line items.
DEVIATION = 1

pytest_param_all_query_param = [
    pytest.param(None, None, id='default'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['account', '*']], id='account_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['account', '*']], id='account_last_30_day'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_two_months_ago'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['account', '*'], ['service', '*']], id='account_service_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['account', '*'], ['service', '*']], id='account_service_last_30_day'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*'], ['service', '*']], id='account_service_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*'], ['service', '*']], id='account_service_two_months_ago'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['service', '*'], ['account', '*']], id='service_account_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['service', '*'], ['account', '*']], id='service_account_two_months_ago'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*'], ['service', '*']], id='account_service_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*'], ['service', '*']], id='account_service_two_months_ago-daily'),
]


@pytest.mark.parametrize("report_filter,group_by", pytest_param_all_query_param)
def test_validate_storage(session_customers, report_filter, group_by):
    """Test to validate the total storage usage across daily and monthly query
    parameters. The total storage usage should be equal to the sum of storage
    usage from the individual line items.
    """

    for customer in session_customers.values():
        report = KokuStorageReport(customer.owner.client)
        report.get(report_filter=report_filter, group_by=group_by)

        # Calculate sum of storage used from individual line items
        storage_used = report.calculate_total()

        if storage_used is None:
            assert len(report.report_line_items()) == 0, (
                "Total storage used is None but the report shows storage usage")
        else:
            assert report.total['value'] - DEVIATION <= storage_used <= \
                report.total['value'] + DEVIATION, (
                'Report total is not equal to the sum of storage used from \
                individual items')
