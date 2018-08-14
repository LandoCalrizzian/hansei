import fauxfactory
import pytest
import uuid

from requests.exceptions import HTTPError

from hansei import config
from hansei.exceptions import KokuException
from hansei.koku_models import KokuServiceAdmin
from hansei.tests.api.conftest import HanseiBaseTestAPI


@pytest.mark.smoke
class TestUserNegativeInput(HanseiBaseTestAPI):
    def test_user_create_no_username(self, new_customer):
        """Try to create a new user without username"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            new_customer.create_user(
                username='',
                email='user_{0}@{0}.com'.format(uniq_string),
                password='redhat')
            raise KokuException("User was created with no username")
        except HTTPError:
            pass

    def test_user_create_no_email(self, new_customer):
        """Try to create a new user without email"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            new_customer.create_user(
                username='user_{}'.format(uniq_string),
                email='',
                password='redhat')
            raise KokuException("User was created with no email")
        except HTTPError:
            pass

    def test_user_create_email_invalid_format(self, new_customer):
        """Try to create a new user with invalid email format"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            new_customer.create_user(
                username='user_{}'.format(uniq_string),
                email='user_{0}{0}.com'.format(uniq_string),
                password='redhat')
            raise KokuException("User was created with an invalid email format")
        except HTTPError:
            pass

    def test_user_delete_invalid_uuid(self, new_customer):
        """Try to delete user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            new_customer.delete_user(uuid.uuid1())
            raise KokuException("User delete was successful with an invalid uuid")
        except HTTPError:
            pass

    def test_user_get_invalid_uuid(self, new_customer):
        """Try to get user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            new_customer.read_user(uuid.uuid1())
            raise KokuException("User retrieval was successful with an invalid uuid")
        except HTTPError:
            pass

#Bugz Filed for failing user preference tests
#https://github.com/project-koku/koku/issues/308
#https://github.com/project-koku/koku/issues/309
@pytest.mark.skip(reason="User preferences validation will be implemented in Release 2")
@pytest.mark.smoke
class TestUserPreferenceNegativeInput(HanseiBaseTestAPI):
    def test_user_preference_create_no_name(self, new_user):
        new_user.login()

        try:
            new_user.create_preference(
                name=None,
                preference={'currency': 'USD'},
                description='Negative Preference Description')
            raise KokuException("User preference was created with no name")
        except HTTPError:
            pass

    def test_user_preference_create_no_preference(self, new_user):
        new_user.login()

        try:
            new_user.create_preference(
                name='currency',
                preference=None,
                description='Negative Preference Description')
            raise KokuException("User preference was created with no preference")
        except HTTPError:
            pass

    @pytest.mark.parametrize("pref_name,pref_value", [
        ['currency', 'Hugs'],
        ['locale', 'en_FOO.LOL-EIGHT'],
        ['timezone', 'LOL']])
    def test_user_preference_create_invalid_preference(self, new_user, pref_name, pref_value):
        new_user.login()

        try:
            new_user.create_preference(
                name=pref_name,
                preference={pref_name: pref_value},
                description='Invalid {} value: {}'.format(pref_name, pref_value))
            raise KokuException(
                "{} user preference was created with an invalid value: {}".format(
                    pref_name, pref_value))

        except HTTPError:
            pass

    def test_user_preference_create_duplicate(self, new_user):
        new_user.login()

        preference_list = new_user.list_preferences()

        orig_preference = preference_list.pop()

        try:
            new_user.create_preference(
                name=orig_preference['name'],
                preference=orig_preference['preference'],
                description=orig_preference['description'])
            raise KokuException('Duplicate user preference was created successfully')

        except HTTPError:
            pass

    def test_user_preference_delete_invalid_uuid(self, new_user):
        new_user.login()

        try:
            new_user.delete_preference(uuid.uuid1())
            raise KokuException("User preference with an invalid uuid was deleted")
        except HTTPError:
            pass

    def test_user_preference_get_invalid_preference_uuid(self, new_user):
        new_user.login()

        try:
            new_user.read_preference(uuid.uuid1())
            raise KokuException("User preference was retrieved with invalid preference")
        except HTTPError:
            pass

    def test_user_preference_update_invalid_preference_uuid(self, new_user):
        new_user.login()

        new_user.create_preference(
            name='editor',
            preference={'editor': 'vim'},
            description='Negative Preference Description')
        pref_uuid = new_user.last_response.json()['uuid']

        try:
            new_user.update_preference(
                uuid.uuid1(),
                name='editor',
                preference={'editor': 'vim'},
                description='Negative Preference Description')
            raise KokuException("User preference was created with no name")
        except HTTPError:
            pass

    def test_user_preference_update_valid_uuid_invalid_data(self, new_user):
        new_user.login()

        try:
            preference_list = new_user.list_preferences()

            # This should fail so grab the first preference uuid in the list
            pref_uuid = preference_list[0]['uuid']
            new_user.update_preference(
                pref_uuid,
                name='fake_pref',
                preference={'fake_pref': 'XXX'},
                description='Invalid preference name allowed for valid preference uuid')
            raise KokuException('Invalid preference name allowed for valid preference uuid')

        except HTTPError:
            pass

    @pytest.mark.parametrize("pref_name,pref_value", [
        ['currency', 'Hugs'],
        ['locale', 'en_FOO.LOL-EIGHT'],
        ['timezone', 'LOL']])
    def test_user_preference_update_invalid_data(self, new_user, pref_name, pref_value):
        new_user.login()

        try:
            preference_list = new_user.list_preferences()

            # This should fail so grab the first preference uuid in the list
            pref_uuid = next((
                pref['uuid'] for pref in preference_list if pref_name in pref['preference'].keys()))

            new_user.update_preference(
                pref_uuid,
                name=pref_name,
                preference={pref_name: pref_value},
                description='Invalid {} value: {}'.format(pref_name, pref_value))
            raise KokuException(
                "{} user preference was updated with an invalid value: {}".format(
                    pref_name, pref_value))

        except HTTPError:
            pass
