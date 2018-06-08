import fauxfactory
import pytest

from kokuqe.koku_models import KokuCustomer, KokuUser


class TestCustomerCrud(object):
    """Create a new customer, read the customer data from the server and delete the customer"""

    @pytest.fixture(scope='class')
    def customer(self):
        """Create a new Koku customer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name='Customer {}'.format(uniq_string)
        owner={
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        #TODO: Implement lazy authentication of the client for new KokuObject()
        return KokuCustomer(name=name, owner=owner)


    def test_customer_create(self, customer):
        customer.create()

        assert customer.uuid, 'No customer uuid created for customer'

    def test_customer_read(self, customer):
        server_customer = customer.read().json()

        assert server_customer['uuid'] == customer.uuid, 'Customer info cannot be read from the server'

        customer_list_response = customer.list().json()
        assert customer_list_response['count'] > 0, 'No customers available on server'

        customer_uuid_list = [cust['uuid'] for cust in customer_list_response['results']]
        assert customer.uuid in customer_uuid_list, 'Customer uuid is not listed in the Koku server list'


    @pytest.mark.skip(reason="Customer update not implemented")
    def test_customer_update(self, customer):
        assert 0

    def test_customer_delete(self, customer):
        customer.delete()
        response = customer.list()

        response_results = response.json()['results']
        for cust in response_results:
            assert cust['uuid'] != customer.uuid, "Customer was not deleted from the koku server"

