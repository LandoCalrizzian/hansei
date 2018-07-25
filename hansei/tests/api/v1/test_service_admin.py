import fauxfactory
import pytest

from hansei.koku_models import KokuServiceAdmin, KokuCustomer, KokuUser

@pytest.mark.smoke
def test_customer_list(koku_config, service_admin):
    assert service_admin.get_current_user().json()['username'] == service_admin.username
