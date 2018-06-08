import fauxfactory
import pytest

from kokuqe import config
from kokuqe.koku_models import KokuCustomer, KokuServiceAdmin, KokuUser


class TestCustomerCrud(object):
    """Create a new customer, read the customer data from the server and delete the customer"""

    @pytest.fixture(scope='class')
    def service_admin(self):
        koku_config = config.get_config().get('koku', {})

        return KokuServiceAdmin(
            username=koku_config.get('username'), password=koku_config.get('password'))

    @pytest.fixture(scope='class')
    def customer(self, service_admin):
        """Create a new Koku customer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        #TODO: Implement lazy authentication of the client for new KokuObject()
        return service_admin.create_customer(name=name, owner=owner)

    def test_customer_create(self, customer):
        assert True
        assert customer.uuid, 'No customer uuid created for customer'

    def test_customer_read(self, service_admin, customer):
        server_customer = service_admin.read_customer(customer.uuid)

        assert server_customer.uuid == customer.uuid, (
            'Customer info cannot be read from the server')

        customer_list = service_admin.list_customers()
        assert len(customer_list) > 0, 'No customers available on server'

        customer_uuid_list = [cust.uuid for cust in customer_list]
        assert customer.uuid in customer_uuid_list, (
            'Customer uuid is not listed in the Koku server list')


    @pytest.mark.skip(reason="Customer update not implemented")
    def test_customer_update(self, customer):
        assert 0

    def test_customer_delete(self, service_admin, customer):
        service_admin.delete_customer(customer.uuid)
        customer_list = service_admin.list_customers()

        for cust in customer_list:
            assert cust.uuid != customer.uuid, "Customer was not deleted from the koku server"

