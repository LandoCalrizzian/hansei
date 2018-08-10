# -*- coding: utf-8 -*-
"""Tests for instance trend inventory report API

The tests assume that the database is pre-populated with data including the
Koku default 'test_customer' customer by running 'make oc-create-test-db-file'.
"""
import pytest
from hansei.koku_models import KokuInstanceReport, KokuCustomer

pytest_param_all_query_param = [
    pytest.param(None, None, id='default'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['account', '*']], id='account_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['account', '*']], id='account_last_30_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['service', '*']], id='service_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['service', '*']], id='service_last_30_day'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_two_months_ago'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['service', '*']], id='service_last_month'),
    pytest.param({'resolution': 'monthly', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['service', '*']], id='service_two_months_ago'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['account', '*']], id='account_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['service', '*']], id='service_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['service', '*']], id='service_two_months_ago-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['account', '*'], ['service', '*']], id='account_service_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['account', '*'], ['service', '*']], id='account_service_last_30_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -10, 'time_scope_units': 'day'},
                 [['service', '*'], ['account', '*']], id='service_account_last_10_day'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -30, 'time_scope_units': 'day'},
                 [['service', '*'], ['account', '*']], id='service_account_last_30_day'),
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
    pytest.param({'resolution': 'daily', 'time_scope_value': -1, 'time_scope_units': 'month'},
                 [['service', '*'], ['account', '*']], id='service_account_last_month-daily'),
    pytest.param({'resolution': 'daily', 'time_scope_value': -2, 'time_scope_units': 'month'},
                 [['service', '*'], ['account', '*']], id='service_account_two_months_ago-daily'),
]


@pytest.mark.parametrize("report_filter,group_by", pytest_param_all_query_param)
def test_validate_instance_uptime(session_customers, report_filter, group_by):
    """Test to validate the total instance uptime across daily and monthly query
    parameters. The total instance uptime should be equal to the sum of instance
    uptime from the individual line items.
    """

    for customer in session_customers.values():
        report = KokuInstanceReport(customer.owner.client)
        report.get(report_filter=report_filter, group_by=group_by)

        # Get total VM uptime of all instances by adding individual items in the report
        vm_uptime = report.calculate_total()

        if vm_uptime is None:
            assert len(report.report_line_items()) == 0, (
                'VM uptime is None but the report shows instances')
        else:
            assert report.total['value'] == vm_uptime, (
                'Report total is not equal to the sum of VM uptime from \
                individual items')
