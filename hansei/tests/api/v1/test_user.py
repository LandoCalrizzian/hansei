import fauxfactory
import pytest
import uuid

from requests.exceptions import HTTPError

from hansei import config
from hansei.exceptions import KokuException
from hansei.koku_models import KokuServiceAdmin


@pytest.mark.smoke
class TestUserNegativeInput(object):
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
        customer = service_admin.create_customer(name=name, owner=owner)
        customer.login()
        assert customer.uuid, 'No customer uuid created for customer'

        yield customer

        service_admin.delete_customer(customer.uuid)

    @pytest.fixture(scope='class')
    def user(self, customer):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
        user = customer.create_user(
            username='user_{}'.format(uniq_string),
            email='user_{0}@{0}.com'.format(uniq_string),
            password='redhat')

        return user

    def test_user_create_no_username(self, customer):
        """Try to create a new user without username"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='',
                email='user_{0}@{0}.com'.format(uniq_string),
                password='redhat')
            raise KokuException("User was created with no username")
        except HTTPError:
            pass

    def test_user_create_no_email(self, customer):
        """Try to create a new user without email"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='user_{}'.format(uniq_string),
                email='',
                password='redhat')
            raise KokuException("User was created with no email")
        except HTTPError:
            pass

    def test_user_create_email_invalid_format(self, customer):
        """Try to create a new user with invalid email format"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='user_{}'.format(uniq_string),
                email='user_{0}{0}.com'.format(uniq_string),
                password='redhat')
            raise KokuException("User was created with an invalid email format")
        except HTTPError:
            pass

    def test_user_delete_invalid_uuid(self, customer):
        """Try to delete user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            customer.delete_user(uuid.uuid1())
            raise KokuException("User delete was successful with an invalid uuid")
        except HTTPError:
            pass

    def test_user_get_invalid_uuid(self, customer):
        """Try to get user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            customer.read_user(uuid.uuid1())
            raise KokuException("User retrieval was successful with an invalid uuid")
        except HTTPError:
            pass
