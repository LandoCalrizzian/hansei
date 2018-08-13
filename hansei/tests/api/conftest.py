"""Pytest customizations and fixtures for the koku tests."""
import fauxfactory
import pytest

from requests.exceptions import HTTPError

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
    Walks the list of non-crud customers specified in the yaml config and adds
    them to the server if they do not exist.

    Returns:
        Dictionary:
            Key: owner email
            Value: ``hansei.koku_models.KokuCustomer`` object
    """
    server_customers = dict([
        [customer.owner.email, customer] for customer in service_admin.list_customers()])

    customer_dict = {}

    for yaml_customer in customer_config:
        # Skip loading any customer w/ a 'crud' tag
        if 'crud' in yaml_customer.get('tags', []):
            continue

        owner_email = yaml_customer['owner']['email']
        if owner_email not in server_customers:
            new_customer = service_admin.create_customer(
                name=yaml_customer['name'], owner=yaml_customer['owner'])

            new_customer.login()

            for config_provider in yaml_customer['providers'] or []:
                new_customer.create_provider(
                    name=config_provider['name'],
                    authentication=config_provider['authentication'],
                    provider_type=config_provider['type'],
                    billing_source=config_provider['billing_source'])


            for config_user in yaml_customer['users'] or []:
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
            # Add the existing customer to the dictionary and
            # Set the password for the KokuCustomer object and login()
            customer_dict[owner_email] = server_customers[owner_email]
            customer_dict[owner_email].owner.password = yaml_customer['owner']['password']
            customer_dict[owner_email].login()

    return customer_dict

class HanseiBaseTestAPI(object):
    @pytest.fixture(scope='class')
    def config_crud_customer(self, customer_config):
        """ Find the first customer in the config that is tagged as CRUD """
        yaml_customer = next(
            (customer for customer in customer_config if 'crud' in customer.get('tags', [])), None)

        assert yaml_customer, "No customer tagged as 'crud' was found in the config"

        return yaml_customer

    @pytest.fixture(scope='class')
    def crud_customer(self, config_crud_customer, service_admin):
        """ Create a customer from the config that has been tagged as crud """
        if not config_crud_customer['owner']['password']:
            config_crud_customer['owner']['password'] = 'redhat'

        customer = service_admin.create_customer(
            config_crud_customer['name'], config_crud_customer['owner'])

        assert customer, "No CRUD customer was created"

        customer.login()

        yield customer

        try:
            # Perform clean up of the crud customer if it exists
            if service_admin.read_customer(customer.uuid):
                service_admin.delete_customer(customer.uuid)
        except HTTPError:
            # Ignore exception since the customer may have been cleaned up
            # by the calling test
            pass

    @pytest.fixture(scope='class')
    def crud_users(self, config_crud_customer, crud_customer):
        """ Create a new user(s) based off the crud customer from the config """
        users = []

        for config_user in config_crud_customer['users'] or []:
            user = crud_customer.create_user(
                username=config_user['username'],
                email=config_user['email'],
                password=config_user['password'] or 'redhat')

            assert  user.login(), "No token assigned to the user after login"

            assert user.uuid, "No uuid was assigned to this user"

            users.append(user)

        # These users will be deleted automatically when the customer is deleted
        return users

    @pytest.fixture(scope='class')
    def new_customer(self, service_admin):
        """Create a new KokuCustomer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'hansei_owner_{}'.format(uniq_string),
            'email': 'hansei_owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        customer = service_admin.create_customer(name=name, owner=owner)
        yield customer

        try:
            # Cleanup this customer if it has an assigned uuid
            if customer.uuid:
                service_admin.delete_customer(customer.uuid)
        except HTTPError:
            # Ignore exception since the customer may have been cleaned up
            # by the calling test
            pass


    @pytest.fixture(scope='class')
    def new_user(self, new_customer):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        if not new_customer.logged_in:
            new_customer.login()

        user= new_customer.create_user(
            username='hansei_user_{}'.format(uniq_string),
            email='hansei_user_{0}@{0}.com'.format(uniq_string),
            password='redhat')

        # This user will be deleted automatically when the customer is deleted
        return user


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
