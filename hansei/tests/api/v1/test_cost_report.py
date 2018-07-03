# -*- coding: utf-8 -*-
"""Tests for cost report API

The tests assume that the database is pre-populated with data including the
Koku default 'test_customer' customer by running 'make oc-create-test-db-file'.
"""
import decimal
from hansei.koku_models import KokuCostReport, KokuCustomer

# Allowed deviation between the reported total cost and the summed up daily
# costs.
DEVIATION = 1

def test_validate_totalcost():
    """Test to validate the total cost.The total cost should be equal to the sum
    of all the daily costs"""


    # Login as test_customer
    customer = KokuCustomer(owner={'username': 'test_customer',
                            'password': 'str0ng!P@ss', 'email': 'foo@bar.com'})

    customer.login()
    report = KokuCostReport(customer.client)
    report.get()

    # Calculate sum of daily costs 
    cost_sum = total_cost = report.calculate_total()

    assert report.total['value'] - DEVIATION <= cost_sum <= \
        report.total['value'] + DEVIATION, \
        'Report total is not equal to the sum of daily costs'
