import fauxfactory
import pytest
import uuid
from requests.exceptions import HTTPError

from hansei.exceptions import KokuException
from hansei.tests.api.conftest import HanseiBaseTestAPI


@pytest.mark.smoke
class TestCustomerCrud(HanseiBaseTestAPI):
    """Create a new customer, read the customer data from the server and delete
    the customer
    """

    def test_customer_create_no_name(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = ''
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }
        try:
            service_admin.create_customer(name=name, owner=owner)
            raise KokuException("Customer created with no name")
        except HTTPError:
            pass

    def test_customer_create_no_owner(self, service_admin):
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)

        try:
            service_admin.create_customer(name=name, owner=None)
            raise KokuException("Customer created with no owner")
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
            raise KokuException("Customer created with no owner username")
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
            raise KokuException("Customer created with no owner email")
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
            raise KokuException("Customer created with invalid owner email")
        except HTTPError:
            pass

    def test_customer_delete_invalid_uuid(self, service_admin):
        """Try to delete customer with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            service_admin.delete_customer(uuid.uuid1())
            raise KokuException("Customer deleted with invalid uuid")
        except HTTPError:
            pass
