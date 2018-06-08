"""Pytest customizations and fixtures for the quipucords tests."""
import fauxfactory
import pytest

from kokuqe import config
from kokuqe.koku_models import KokuServiceAdmin, KokuCustomer, KokuUser

@pytest.fixture
def koku_config():
    return config.get_config().get('koku', {})

@pytest.fixture
def service_admin(koku_config):
    return KokuServiceAdmin(username = koku_config.get('username'), password = koku_config.get('password'))

@pytest.fixture
def new_customer(service_admin):
    """Create a new KokuCustomer with random info"""
    uniq_string = fauxfactory.gen_string('alphanumeric', 8)
    name='Customer {}'.format(uniq_string)
    owner={
        'username': 'owner_{}'.format(uniq_string),
        'email': 'owner_{0}@{0}.com'.format(uniq_string),
        'password': 'redhat', }

    return service_admin.create_customer(name=name, owner=owner)


@pytest.fixture
def new_user(new_customer):
    """Create a new Koku user without authenticating to the server"""
    uniq_string = fauxfactory.gen_string('alphanumeric', 8)
    new_customer.login()

    return new_customer.create_user(
        username='user_{}'.format(uniq_string),
        email='user_{0}@{0}.com'.format(uniq_string),
        password='redhat')
