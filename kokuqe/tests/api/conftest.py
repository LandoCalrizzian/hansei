"""Pytest customizations and fixtures for the quipucords tests."""
import fauxfactory
import pytest

from kokuqe import config
from kokuqe.koku_models import KokuCustomer, KokuUser

@pytest.fixture
def koku_config():
    return config.get_config().get('koku', {})


@pytest.fixture
def new_customer():
    """Create a new Koku Kcustomer with random info"""
    uniq_string = fauxfactory.gen_string('alphanumeric', 8)
    name='Customer {}'.format(uniq_string)
    owner={
        'username': 'owner_{}'.format(uniq_string),
        'email': 'owner_{0}@{0}.com'.format(uniq_string),
        'password': 'redhat', }

    #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
    return KokuCustomer(name=name, owner=owner)


@pytest.fixture
def new_user():
    """Create a new Koku user without authenticating to the server"""
    uniq_string = fauxfactory.gen_string('alphanumeric', 8)

    #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
    return KokuUser(
        username='user_{}'.format(uniq_string),
        email='user_{0}@{0}.com'.format(uniq_string),
        password='redhat')
