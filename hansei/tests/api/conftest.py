"""Pytest customizations and fixtures for the koku tests."""
import fauxfactory
import pytest

from hansei import config
from hansei.koku_models import KokuServiceAdmin


@pytest.fixture(scope='session')
def koku_config():
    return config.get_config().get('koku', {})

@pytest.fixture(scope='session')
def customer_config():
    return config.get_config().get('customers', {})


@pytest.fixture(scope='session')
def service_admin(koku_config):
    """
    Create a KokuServiceAdmin object that is valid for the entire session
    This admin will be authenticate upon instantiation
    """
    admin = KokuServiceAdmin(
        username=koku_config.get('username'), password=koku_config.get('password'))

    admin.login()

    return admin


@pytest.fixture(scope='session')
def session_customers(customer_config, service_admin):
    """
    Get a dictionary of the existing customers and all of the customers/users/providers
    specified in the yaml config

    Returns:
        Dictionary:
            Key: owner email
            Value: ``hansei.koku_models.KokuCustomer`` object
    """
    customer_dict = dict([
        [customer.owner.email, customer] for customer in service_admin.list_customers()])

    for config_customer in customer_config:
        # Skip loading any customer w/ a 'crud' tag
        if 'crud' in config_customer.get('tags', []):
            continue

        owner_email = config_customer['owner']['email']
        if owner_email not in customer_dict:
            new_customer = service_admin.create_customer(
                name=config_customer['name'], owner=config_customer['owner'])

            new_customer.login()

            for config_provider in config_customer['providers'] or []:
                new_customer.create_provider(
                    name=config_provider['name'],
                    authentication=config_provider['authentication'],
                    provider_type=config_provider['type'],
                    billing_source=config_provider['billing_source'])


            for config_user in config_customer['users'] or []:
                new_customer.create_user(
                    username=config_user['username'],
                    email=config_user['email'],
                    password=config_user['password'])

                for config_provider in config_user['providers'] or []:
                    new_user.create_provider(
                        name=config_provider['name'],
                        authentication=config_provider['authentication'],
                        provider_type=config_provider['type'],
                        billing_source=config_provider['billing_source'])

            customer_dict[owner_email] = new_customer
        else:
            # Set the password in the KokuCustomer object and login()
            customer_dict[owner_email].owner.password = config_customer['owner']['password']
            customer_dict[owner_email].login()

    return customer_dict

class HanseiBaseTestAPI(object):
    @pytest.fixture(scope='class')
    def new_customer(self, service_admin):
        """Create a new KokuCustomer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        return service_admin.create_customer(name=name, owner=owner)

    @pytest.fixture(scope='class')
    def new_user(self, new_customer):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        if not new_customer.logged_in:
            new_customer.login()

        return new_customer.create_user(
            username='user_{}'.format(uniq_string),
            email='user_{0}@{0}.com'.format(uniq_string),
            password='redhat')

    @pytest.fixture(scope='class')
    def new_provider(self, new_user):
        """Create a new KokuProvider"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        # Grab the first AWS provider
        provider_config = [
            prov for prov in config.get_config().
            get('providers', {})if prov['type'] == 'AWS'][0]

        if not new_user.logged_in:
            new_user.login()

        # TODO: Implement lazy authentication of the client for new
        # KokuObject() fixtures
        provider = new_user.create_provider(
            name='Provider {} for user {}'.format(
                uniq_string, new_user.username),
            authentication=provider_config.get('authentication'),
            provider_type=provider_config.get('type'),
            billing_source=provider_config.get('billing_source'))

        return provider
