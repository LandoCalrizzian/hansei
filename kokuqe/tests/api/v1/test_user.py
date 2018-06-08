import fauxfactory
import pytest

from kokuqe.koku_models import KokuCustomer, KokuUser


class TestUserCrud(object):
    @pytest.fixture(scope='class')
    def customer(self):
        """Create a new Koku customer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
        customer = KokuCustomer(name=name, owner=owner)
        customer.create()
        assert customer.uuid, 'No customer uuid created for customer'

        yield customer

        # Login as the admin user to delete the customer
        customer.client.login()
        customer.delete()

    @pytest.fixture(scope='class')
    def user(self):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
        return KokuUser(
            username='user_{}'.format(uniq_string),
            email='user_{0}@{0}.com'.format(uniq_string),
            password='redhat')


    def test_user_create(self, customer, user):
        """Create a new user, read the user data from the server and delete the user"""
        # Login as the newly created customer user
        customer.client.login(
            username=customer.owner['username'], password=customer.owner['password'])

        # Use the token auth associated with the customer owner
        user.client.token = customer.client.token

        # All requests will throw an exception if response is an error code
        response = user.create()
        assert user.uuid, 'No uuid created for user'


    def test_user_read(self, user):
        server_user = user.read().json()

        # TODO: Overload equivalence for KokuObjects
        assert server_user['uuid'] == user.uuid, 'User info cannot be read from the server'

        user_list_response = user.list().json()
        assert user_list_response['count'] > 0, 'No users available on server'

        user_uuid_list = [cust['uuid'] for cust in user_list_response['results']]
        assert user.uuid in user_uuid_list, 'user uuid is not listed in the Koku server list'


    @pytest.mark.skip(reason="User update not implemented")
    def test_user_update(self):
        assert 0

    def test_user_update_preference(self, user):
        name = 'editor'
        preference = {name: 'vim', }
        #TODO: Refactor KokuObjects so that the client always matches the class context for auth
        with user:
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

    def test_user_delete(self, customer, user):
        user.delete()
        response = user.list()

        response_results = response.json()['results']
        for server_user in response_results:
            assert server_user['uuid'] != user.uuid, "User was not deleted from the koku server"
