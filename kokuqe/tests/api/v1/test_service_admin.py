import fauxfactory
import pytest

from kokuqe.koku_models import KokuServiceAdmin, KokuCustomer, KokuUser

def test_customer_list(koku_config, service_admin):
    assert service_admin.get_current_user().json()['username'] == service_admin.username
