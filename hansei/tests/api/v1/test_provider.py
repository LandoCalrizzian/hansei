import fauxfactory
import pytest

from hansei import config
from hansei.koku_models import KokuCustomer, KokuProvider, KokuServiceAdmin, KokuUser


@pytest.mark.smoke
class TestProviderNegative(object):
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

        user.login()
        yield user

        customer.delete_user(user.uuid)

    @pytest.fixture(scope='class')
    def provider(self, user):
        """Create a new KokuProvder"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        #Grab the first AWS provider
        provider_config = [
            prov for prov in config.get_config().get('providers', {}) if prov['type'] == 'AWS'][0]

        #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
        provider = user.create_provider(
            name='Provider {} for user {}'.format(uniq_string, user.username),
            authentication=provider_config.get('authentication'),
            provider_type=provider_config.get('type'),
            billing_source=provider_config.get('billing_source'))

        return provider
