import fauxfactory
import pytest
import uuid
from requests.exceptions import HTTPError

from hansei.tests.api.conftest import HanseiBaseTestAPI


@pytest.mark.smoke
class TestOnboardingCRUD(HanseiBaseTestAPI):
    """ Test the CRUD operations for onboarding of customers, users, providers """

    @pytest.fixture(scope='class')
    def config_crud_customer(self, customer_config):
        """ Find the first customer in the config that is tagged as CRUD """
        config_customer = next(
            (customer for customer in customer_config if 'crud' in customer['tags']), None)

        assert config_customer, "No customer tagged as 'crud' was found in the config"

        return config_customer

    @pytest.fixture(scope='class')
    def crud_customer(self, config_crud_customer, service_admin):
        if not config_crud_customer['owner']['password']:
            config_crud_customer['owner']['password'] = 'redhat'

        customer = service_admin.create_customer(
            config_crud_customer['name'], config_crud_customer['owner'])

        assert customer, "No CRUD customer was created"

        customer.login()

        return customer

    @pytest.fixture(scope='class')
    def crud_users(self, config_crud_customer, crud_customer):
        """ Create a new user(s) based off the crud customer from the config """
        users = []

        for config_user in config_crud_customer['users']:
            user = crud_customer.create_user(
                username=config_user['username'],
                email=config_user['email'],
                password=config_user['password'] or 'redhat')

            assert  user.login(), "No token assigned to the user after login"

            assert user.uuid, "No uuid was assigned to this user"

            users.append(user)

        return users

    def test_customer_create(self, service_admin, crud_customer):
        assert crud_customer.uuid, (
            "Customer {} was not assigned a UUID".format(crud_customer.name))

    def test_customer_read(self, service_admin, crud_customer):
        server_customer = service_admin.read_customer(crud_customer.uuid)
        customer_list = service_admin.list_customers()

        assert len(customer_list) > 0, 'No customers available on server'

        assert server_customer.uuid == crud_customer.uuid, (
            'Customer info cannot be read from the server')

        customer_uuid_list = [cust.uuid for cust in customer_list]
        assert crud_customer.uuid in customer_uuid_list, (
            'Customer uuid is not listed in the Koku server list')

    @pytest.mark.skip(reason="Customer update not implemented")
    def test_customer_update(self):
        assert 0

    ############################################################################
    # USER CRUD
    ############################################################################
    def test_user_read(self, crud_customer, crud_users):
        """ Verify that the user(s) we added can be retrieved from the server """

        user_list = crud_customer.list_users()
        assert len(user_list) > 0, 'No users available on server'

        user_uuid_list = [usr.uuid for usr in user_list]

        for user in crud_users:
            server_user = crud_customer.read_user(user.uuid)

            assert server_user.uuid == user.uuid, 'User info cannot be read from the server'

            assert user.uuid in user_uuid_list, 'user uuid is not listed in the Koku server list'


    @pytest.mark.skip(reason="User update not implemented")
    def test_user_update(self):
        assert 0

    def test_user_update_preference(self, crud_users):
        """ Verify that we can update the preferences for any user """
        for user in crud_users:
            name = 'editor'
            preference = {name: 'vim', }

            orig_user_pref = user.read_preference().json()['results']

            pref_response = user.create_preference(name=name, preference=preference).json()
            assert pref_response['uuid'], 'New user preference was not assigned a uuid'

            assert pref_response['user']['uuid'] == user.uuid, (
                    'Preference user uuid does not match the current user uuid')

            #TODO: Is string data normalized when saved. Case Normalization, localization, ...
            assert pref_response['name'] == name and pref_response['preference'] == preference, (
                    'Created preference does not match the values supplied during creation')

            orig_pref_response = pref_response
            pref_description = 'There is no other editor choice'
            pref_response = user.update_preference(pref_response['uuid'], description=pref_description).json()

            assert (
                pref_response['description'] == pref_description and
                pref_response['description'] != orig_pref_response['description'] and
                pref_response['name'] == orig_pref_response['name'] and
                pref_response['preference'] == orig_pref_response['preference']), (
                    'Preference was not updated properly')

    ############################################################################
    # User(s) will be deleted during deletion of customer data
    ############################################################################

    ############################################################################
    # PROVIDER CRUD
    ############################################################################

    def test_provider_create(self, config_crud_customer, crud_customer, crud_users):
        """Create any provider's associated with the customer and/or users"""

        for config_provider in config_crud_customer.get('providers') or []:
            provider = crud_customer.create_provider(
                name=config_provider['name'],
                authentication=config_provider['authentication'],
                provider_type=config_provider['type'],
                billing_source=config_provider['billing_source'])

            # All requests will throw an exception if response is an error code
            assert provider.uuid, 'No uuid created for provider'

        for config_user in config_crud_customer.get('users') or []:
            # Loop the the users and add any providers found
            if not config_user.get('providers'):
                continue

            for config_provider in config_user['providers']:
                provider_user = next(
                    (crud_user
                        for crud_user in crud_users if (
                            crud_user.username == config_user['username'])),
                    None)

                assert provider_user, 'Unable to find the crud user to assign provider {}'.format(
                    config_provider['name'])

                provider = provider_user.create_provider(
                    name=config_provider['name'],
                    authentication=config_provider['authentication'],
                    provider_type=config_provider['type'],
                    billing_source=config_provider['billing_source'])

                # All requests will throw an exception if response is an error code
                assert provider.uuid, 'No uuid created for provider'

    def test_provider_read(self, config_crud_customer, crud_customer, crud_users):
        """Read the provider data from the server"""

        # Generate a list of provider info from the config
        config_provider_list = [
            config_provider for config_provider in config_crud_customer.get('providers') or []]

        for config_users in config_crud_customer.get('users') or []:
            config_provider_list.extend(config_users.get('providers') or [])

        provider_list = crud_customer.list_providers()
        assert len(provider_list) > 0, 'No providers available on server'

        # List of providers available to CRUD customer should be the same as providers in the config
        assert len(provider_list) == len(config_provider_list), (
            'The number of providers on the server != the number of providers added in config')

        config_provider_arn_list = [
            provider['authentication']['provider_resource_name']
                for provider in config_provider_list]

        # Perform a shallow check based on the provider ARN
        for provider in provider_list:
            assert provider.authentication['provider_resource_name'] in config_provider_arn_list, (
                'Server provider ARN not found in the providers added from the config')

    ############################################################################
    # Provider(s) will be deleted during deletion of customer data
    ############################################################################

    def test_customer_delete(self, service_admin, crud_customer, crud_users):
        """Verify that upon deletion of customer, all users and providers associated
        with the customer are also deleted.
        """
        user_uuid_list = [user.uuid for user in crud_users]

        service_admin.delete_customer(crud_customer.uuid)
        customer_list = service_admin.list_customers()

        for cust in customer_list:
            assert cust.uuid != crud_customer.uuid, \
                "Customer was not deleted from the koku server"

        user_list = service_admin.list_users()
        for user in user_list:
            assert user.uuid not in user_uuid_list, "A delete user still exists on the server"
