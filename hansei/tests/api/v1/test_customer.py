import fauxfactory
import pytest
import uuid
from requests.exceptions import HTTPError

from hansei.tests.api.conftest import HanseiBaseTestAPI


@pytest.mark.smoke
class TestCustomerCrud(HanseiBaseTestAPI):
    """Create a new customer, read the customer data from the server and delete
    the customer
    """

    def test_customer_create(self, new_user, new_customer):
        assert True
        assert new_customer.uuid, 'No customer uuid created for customer'

    def test_customer_read(self, service_admin, new_customer):
        server_customer = service_admin.read_customer(new_customer.uuid)

        assert server_customer.uuid == new_customer.uuid, (
            'Customer info cannot be read from the server')

        customer_list = service_admin.list_customers()
        assert len(customer_list) > 0, 'No customers available on server'

        customer_uuid_list = [cust.uuid for cust in customer_list]
        assert new_customer.uuid in customer_uuid_list, (
            'Customer uuid is not listed in the Koku server list')

    @pytest.mark.skip(reason="Customer update not implemented")
    def test_customer_update(self, new_customer):
        assert 0

    def test_customer_delete(self, service_admin, new_customer, new_user,
                             new_provider):
        """Verify that upon deletion of customer, all users and providers associated
        with the customer are also deleted.
        """
        service_admin.delete_customer(new_customer.uuid)
        customer_list = service_admin.list_customers()

        for cust in customer_list:
            assert cust.uuid != new_customer.uuid, \
                "Customer was not deleted from the koku server"

        # TODO : In future, verify that the user and provider data has been
        # deleted from the DB

        try:
            new_user.login()
            assert 0, "User data was not deleted from Koku"
        except HTTPError:
            pass

    def test_customer_create_no_name(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = ''
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }
        try:
            service_admin.create_customer(name=name, owner=owner)
        except HTTPError:
            pass

    def test_customer_create_no_owner(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)

        try:
            service_admin.create_customer(name=name, owner='')
        except HTTPError:
            pass

    def test_customer_create_no_owner_username(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': '',
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }
        try:
            service_admin.create_customer(name=name, owner=owner)
        except HTTPError:
            pass

    def test_customer_create_no_owner_email(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': '',
            'password': 'redhat', }
        try:
            service_admin.create_customer(name=name, owner=owner)
        except HTTPError:
            pass

    def test_customer_create_owner_invalid_email(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'user_{0}{0}.com'.format(uniq_string),
            'password': 'redhat', }
        try:
            service_admin.create_customer(name=name, owner=owner)
        except HTTPError:
            pass

    def test_customer_delete_invalid_uuid(self, service_admin):
        """Try to delete customer with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            service_admin.delete_customer(uuid.uuid1())
        except HTTPError:
            pass
