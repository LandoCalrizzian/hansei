import fauxfactory
import pytest

from hansei.koku_models import KokuServiceAdmin, KokuCustomer, KokuUser

@pytest.mark.smoke
def test_customer_list(service_admin, session_customers):
    customer_uniq_dict = dict([[customer.owner.email, customer.uuid] for customer in service_admin.list_customers()])

    for owner_email, customer in session_customers.items():
        assert owner_email in customer_uniq_dict, (
            "Could not find {} in the list of customers".format(customer.name))

        assert customer_uniq_dict[owner_email] == customer.uuid, (
            "The customer {} with uuid {} did not match the expected customer uuid {}".format(
                customer.name, customer.uuid, customer_uniq_dict[owner_email]))
