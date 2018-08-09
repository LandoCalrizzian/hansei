import fauxfactory
import pytest
import uuid

from requests.exceptions import HTTPError

from hansei import config
from hansei.koku_models import KokuCustomer, KokuProvider, KokuServiceAdmin, KokuUser
from hansei.tests.api.conftest import HanseiBaseTestAPI

@pytest.mark.smoke
class TestProviderNegative(HanseiBaseTestAPI):
    @pytest.fixture(scope='class')
    def provider_config(self, config_crud_customer):
        """ Traverse the customer config to find a valid provider to use for negative testing """
        provider = None
        if config_crud_customer.get('providers'):
            return next((provider for provider in config_crud_customer['providers']), None)

        for user in config_crud_customer.get('users') or []:
            if user.get('providers'):
                return next((provider for provider in user['providers']), None)

        return None

    def test_provider_create_no_name(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=None,
                authentication=provider_config['authentication'],
                provider_type=provider_config['type'],
                billing_source=provider_config['billing_source'])
            raise KokuException("Provider was created with no name")
        except HTTPError:
            pass

    def test_provider_create_no_type(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=provider_config['name'],
                authentication=provider_config['authentication'],
                provider_type=None,
                billing_source=provider_config['billing_source'])
            raise KokuException("Provider was created with no type")
        except HTTPError:
            pass

    def test_provider_create_no_type_aws(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=provider_config['name'],
                authentication=provider_config['authentication'],
                provider_type='FOO',
                billing_source=provider_config['billing_source'])
            raise KokuException("Provider was created with type other than aws")
        except HTTPError:
            pass

    def test_provider_create_no_aws_resource_name(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=provider_config['name'],
                authentication=None,
                provider_type=provider_config['type'],
                billing_source=provider_config['billing_source'])
            raise KokuException("Provider was created with no resource name")
        except HTTPError:
            pass

    def test_provider_create_no_billing_source(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=provider_config['name'],
                authentication=provider_config['authentication'],
                provider_type=provider_config['type'],
                billing_source=None)
            raise KokuException("Provider was created with no billing source")
        except HTTPError:
            pass

    def test_provider_create_no_bucket(self, crud_customer, provider_config):
        try:
            crud_customer.create_provider(
                name=provider_config['name'],
                authentication=provider_config['authentication'],
                provider_type=provider_config['type'],
                billing_source={'bucket': None})
            raise KokuException("Provider was created with no bucket")
        except HTTPError:
            pass

    def test_provider_delete_invalid_uuid(self, crud_customer, provider_config):
        """Try: to delete a provider using an invalid uuid"""

        try:
            crud_customer.delete_provider(uuid.uuid1())
            raise KokuException("Provider delete was successful with an invalid uuid")
        except HTTPError:
            pass

    def test_provider_get_invalid_uuid(self, crud_customer, provider_config):
        """Try: to get a provider using an invalid uuid"""

        try:
            crud_customer.read_user(uuid.uuid1())
            raise KokuException("Provider retrieval was successful with an invalid uuid")
        except HTTPError:
            pass
