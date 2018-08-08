# coding: utf-8
"""Models for use with the Koku API."""

import decimal
from pprint import pformat
from urllib.parse import urljoin

from hansei import api, config
from hansei.exceptions import KokuException
from hansei.constants import (
    KOKU_DEFAULT_USER,
    KOKU_DEFAULT_PASSWORD,
    KOKU_CUSTOMER_PATH,
    KOKU_USER_PATH,
    KOKU_PROVIDER_PATH,
    KOKU_COST_REPORTS_PATH,
    KOKU_STORAGE_REPORTS_PATH,
    KOKU_INSTANCE_REPORTS_PATH
)


class KokuObject(object):
    """A base class for other KOKU models.

    Child classes should define member variables that match the names and format supplied in a POST
    request used to create this object on the koku server
    """

    def __init__(
            self,
            client=None,
            uuid=None,
            authenticate=False):
        """Provide shared methods for KOKU model objects.

        Arguments:
            client - ``hansei.api.Client`` instance used to communicate with the Koku server
            uuid - Koku uuid for the Koku object
        """
        self.uuid = uuid
        self.client = client if client else api.Client(authenticate=authenticate)
        self.endpoint = ''

    def fields(self):
        """Return a dictionary with all fields.

        The fields are all data items that may be returned when a `GET` request
        is sent to the endpoint. It excludes items specific to hansei such as
        the client and endpoint associated with objects of this type.
        """
        fields = self.payload()
        fields['uuid'] = self.uuid
        return fields

    def path(self):
        """Return the path to this object on the server.

        This concatenates the endpoint and the id of this object,
        to be used to read details about this object or to delete it.
        """
        return urljoin(self.endpoint, '{}/'.format(self.uuid))

    def payload(self):
        """Return a dictionary for POST or PUT requests.

        Override this in child objects if you'll have member variable (or variable names) that 
        are not used in POST or PUT data
        """
        return {
            k: v for k, v in vars(self).items()
            if k not in ['uuid',
                         'client',
                         'endpoint',
                        ]
        }

    def update_payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {
            k: v for k, v in vars(self).items()
            if k not in ['uuid',
                         'client',
                         'endpoint',
                        ]
        }

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other

    def get_current_user(self):
        """Send GET request return the user assigned to the client authentication token"""
        return self.client.get_user()

    def _create(self, client=None, **kwargs):
        """Send POST request to the self.endpoint of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            ``request.request()`` method.

        Sends ``self.payload()`` as the data of the POST request, thereby
        creating an object on the server.

        Before returning the requests.models.Response to the caller, the
        ``uuid`` of this object is set using the data from the response.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's ``self.uuid``.
        """
        client = client or self.client

        response = client.post(self.endpoint, self.payload(), **kwargs)
        if response.status_code in range(200, 203):
            self.uuid = response.json().get('uuid')
        return response

    def _list(self, client=None, **kwargs):
        """Send GET request to read all objects of this type.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response
            contains a list of dictionaries with the data associated with each
            object of this type stored on the server.
        """
        client = client or self.client

        return client.get(self.endpoint, **kwargs)

    def _read(self, client=None, **kwargs):
        """Send GET request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self.uuid`.
        """
        client = client or self.client
        return client.get(self.path(), **kwargs)

    def _update(self, client=None, **kwargs):
        """Send PUT request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Sends `self.update_payload()` as the data of the PUT request, thereby
        updating the object on the server with the same `id` as this object
        with the fields contained in `self.update_payload()`.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self.uuid`.
        """
        client = client or self.client

        return client.put(self.path(), self.update_payload(), **kwargs)

    def _delete(self, client=None, **kwargs):
        """Send DELETE request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.
        """
        client = client or self.client

        return client.delete(self.path(), **kwargs)

    #TODO: Refactor payload() & fields()
    def load(self, payload):
        """Populate the object data from the response of a GET request
        Arguments:
            payload - dictionary object from json response
        """
        raise NotImplementedError

    def reload(self):
        """Send a GET request based on the current uuid to reload the current member data"""
        if not self.uuid:
            raise KokuException(
                'Unable to refresh {} object. No uuid specified'.format(self.__class__))

        response = self.read()
        response_data = response.json()

        self_vars = self.payload()
        for key in response_data:
            if key in self_vars:
                setattr(self, key, response_data[key])

    @property
    def last_response(self):
        """Return the response of the most recent Koku rest api call

        Returns ``hansei.api.Client.last_response``
        """
        return self.client.last_response

    @property
    def logged_in(self):
        """Returns True if the client is currently logged in"""
        return self.client.token is not None

    def logout(self):
        """Logout and make current token invalid"""
        self.client.logout()
        return self.client.token is None

    def list_users(self):
        """Retrieve the list of users on the Koku Server

        Returns: List of ``hansei.koku_models.KokuUser`` objects
        """
        user_list = []
        response = self.client.get(KOKU_USER_PATH)

        assert response, 'Unable to retrieve user list in {}.list_users()'.format(
            self.__class__)

        for user_response in response.json()['results']:
            tmp_user = KokuUser()
            tmp_user.load(user_response)
            user_list.append(tmp_user)

        return user_list



class KokuServiceAdmin(KokuObject):
    """Class to perform actions as the Koku Service Admin"""

    def __init__(self, client=None, username=None, password=None):
        """
        Arguments:
            client - existing ``hansei.api.Client`` instance used to communicate with the Koku
                server. client authenticaton credentials will be used even if username & password
                are provided
            username - username to use for authentication
            password - password to use for authentication
        """
        cfg = config.get_config().get('koku', {})
        self.username = username or cfg.get('username', KOKU_DEFAULT_USER)
        self.password = password or cfg.get('password', KOKU_DEFAULT_PASSWORD)

        self.client = client if client else api.Client(
            username=self.username, password=self.password)

        self.uuid = None

    def _create(self, client=None):
        raise NotImplementedError("Cannot create a service admin account")

    def _read(self, client=None):
        raise NotImplementedError("Cannot read a service admin account")

    def _list(self, client=None):
        raise NotImplementedError("Cannot read a service admin account")

    def _update(self, client=None):
        raise NotImplementedError("Cannot update a service admin account")

    def _delete(self, client=None):
        raise NotImplementedError("Cannot delete a service admin account")

    def login(self):
        """Login as the currently assigned service admin user"""
        self.client.login(self.username, self.password)
        return self.client.token is not None

    def create_customer(self, name, owner):
        """Create a Koku Customer object

        Args:
            name - Name of the customer
            owner - Customer owner information
                Dictionary Keys:
                    username - Username for the owner
                    email - Owner email address
                    password - Owner user password

        Returns: ``hansei.koku_models.KokuCustomer`` object
        """
        customer = KokuCustomer(name=name, owner=owner)
        customer._create(self.client)
        return customer

    def read_customer(self, uuid):
        """Get a Koku Customer object with assigned uuid

        Args:
            uuid - Koku uuid of the customer to retrieve

        Returns: ``hansei.koku_models.KokuCustomer`` object
        """
        customer = KokuCustomer(uuid=uuid)
        customer.load(customer._read(self.client).json())
        return customer

    def delete_customer(self, uuid):
        """Delete a Koku Customer object with assigned uuid

        Args:
            uuid - Koku uuid of the customer to delete
        """
        customer = KokuCustomer(uuid=uuid)
        customer._delete(self.client)

    def list_customers(self):
        """Retrieve the list of customers on the Koku Server

        Returns: List of ``hansei.koku_models.KokuCustomer`` objects
        """
        customer_list = []
        self.client.get(KOKU_CUSTOMER_PATH)
        assert self.client.last_response, 'Unable to retrieve customer list in {}.list_customers()'.format(
            self.__class__)

        for customer_response in self.last_response.json()['results']:
            cust = KokuCustomer()
            cust.load(customer_response)
            customer_list.append(cust)

        return customer_list


class KokuCustomer(KokuObject):
    """A class to manage a Koku customer and its users"""

    def __init__(self, client=None, uuid=None, name=None, owner=None):
        """Initialize this object with customer information.

        Arguments:
            client - If None, un-authenticated ``hansei.api.client`` will be created
                else, Existing  object to use for authentication.
                If provided, client authentication should match any supplied
                customer with name.
            uuid - UUID of an existing customer
            name - Name of the customer
            owner - KokuUser object to set as the Customer owner.
                Owner.client will be used for all customer REST API calls
        """
        super().__init__(client=None, uuid=uuid, authenticate=False)
        # If no client specified create ``api.Client`` with no authentication
        self.name = name
        if owner:
            self.owner = KokuUser(
                client=client, **owner)
        else:
            self.owner = KokuUser( client=client, username=None, email=None, password=None)

        self.endpoint = KOKU_CUSTOMER_PATH

    def login(self):
        """Login as the customer owner
        Authentication info is provided by the ``KokuCustomer.owner`` dictionary
        """
        self.owner.login()
        return self.owner.client.token is not None

    def load(self, payload):
        """Populate the object data from the response of a GET request

        Arguments:
            payload - dictionary object from json response
        """
        self.uuid = payload['uuid']
        self.name = payload['name']
        self.owner = KokuUser(**payload['owner'])

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        payload = {
            "name": self.name,
            "owner": self.owner.payload() if self.owner else None,
        }
        return payload

    def create_user(self, username, email, password=None):
        """Create a Koku User object

        Args:
            uuid - UUID of an existing customer
            username - Username for the user
            email - User email address
            password - User password

        Returns: ``hansei.koku_models.KokuUser`` object
        """
        user = KokuUser(username=username, email=email, password=password)
        user._create(self.owner.client)
        return user

    def read_user(self, uuid):
        """Get a Koku User object with assigned uuid

        Args:
            uuid - Koku uuid of the user to retrieve

        Returns: ``hansei.koku_models.KokuUser`` object
        """
        user = KokuUser(uuid=uuid)
        user.load(user._read(self.owner.client).json())
        return user


    def delete_user(self, uuid):
        """Delete a Koku User object with assigned uuid

        Args:
            uuid - Koku uuid of the user to delete
        """
        user = KokuUser(uuid=uuid)
        user._delete(self.owner.client)

    #TODO: This should be in KokuObject since all authenticated 'users' can query
    def list_users(self):
        """Retrieve the list of users on the Koku Server

        Returns: List of ``hansei.koku_models.KokuUser`` objects
        """
        user_list = []
        response = self.owner.client.get(KOKU_USER_PATH)

        assert response, 'Unable to retrieve user list in {}.list_users()'.format(
            self.__class__)

        for user_response in response.json()['results']:
            tmp_user = KokuUser()
            tmp_user.load(user_response)
            user_list.append(tmp_user)

        return user_list

    ################################################################################################
    # Provider
    # TODO: These methods should be refactored so we can use them in KokuCustomer & KokuUser
    ################################################################################################
    def create_provider(self, name, authentication, provider_type, billing_source):
        """Create a Koku Provider
            name - Name for the provider
            authentication - Authentication for the provider
            provider_type - Type of provider
            billing_source - Billing information for the provider
        """
        return self.owner.create_provider(name, authentication, provider_type, billing_source)

    def read_provider(self, uuid):
        """Get a Koku Provider object with assigned uuid

        Args:
            uuid - Koku uuid of the provider to retrieve

        Returns: ``hansei.koku_models.KokuProvider`` object
        """

        return self.owner.read_provider(uuid)

    def list_providers(self):
        """Retrieve the list of providers assigned to the current user

        Returns: List of ``hansei.koku_models.KokProvider`` objects
        """
        return self.owner.list_providers()

    def delete_provider(self, uuid):
        """Delete the provider specified by uuid

        Arguments:
            uuid - Koku uuid of the provider to delete
        """
        self.owner.delete_provider()


class KokuUser(KokuObject):
    """Manage a Koku User account"""

    def __init__(self, client=None, uuid=None, username=None, email=None, password=None):
        """
        Arguments:
            client - Existing `hansei.api.client` object to use for authentication.
                This client authentication will determine what koku features client has access to
            uuid - UUID of an existing customer
            username - Username for the user
            email - User email address
            password - User password
        """
        super().__init__(client=client, uuid=uuid)
        self.username = username
        self.email = email
        self.password = password
        self.endpoint = KOKU_USER_PATH

    def __enter__(self):
        self._orig_token = self.client.token
        self.client.login(self.username, self.password)

    def __exit__(self, *args, **kwargs):
        self.client.token = self._orig_token
        self._orig_token = None

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        payload = {
            "username": self.username,
            "email": self.email,
        }

        if self.password:
            payload['password'] = self.password

        return payload

    def load(self, payload):
        """Populate the object data from the response of a GET request

        Arguments:
            payload - dictionary object from json response
        """
        self.uuid = payload['uuid']
        self.username = payload['username']
        self.email = payload['email']
        self.password = None

    def login(self):
        """Login as the currently assigned user"""
        self.client.login(self.username, self.password)
        return self.client.token is not None

    ################################################################################################
    # Provider
    # TODO: These methods should be refactored so we can use them in KokuCustomer & KokuUser
    ################################################################################################
    def create_provider(self, name, authentication, provider_type, billing_source):
        """Create a Koku Provider
            name - Name for the provider
            authentication - Authentication for the provider
            provider_type - Type of provider
            billing_source - Billing information for the provider
        """
        provider = KokuProvider(
            name=name,
            authentication=authentication,
            provider_type=provider_type,
            billing_source=billing_source)

        provider._create(self.client)
        return provider

    def read_provider(self, uuid):
        """Get a Koku Provider object with assigned uuid

        Args:
            uuid - Koku uuid of the provider to retrieve

        Returns: ``hansei.koku_models.KokuProvider`` object
        """
        provider = KokuProvider(uuid=uuid)
        provider.load(provider._read(self.client).json())
        return provider

    def list_providers(self):
        """Retrieve the list of providers assigned to the current user

        Returns: List of ``hansei.koku_models.KokProvider`` objects
        """
        providerlist = []
        response = self.client.get(KOKU_PROVIDER_PATH)

        assert response, 'Unable to retrieve provider list in KokuUser.list_providers()'

        for provider_response in response.json()['results']:
            tmp_provider = KokuProvider()
            tmp_provider.load(provider_response)
            providerlist.append(tmp_provider)

        return providerlist

    def delete_provider(self, uuid):
        """Delete the provider specified by uuid

        Arguments:
            uuid - Koku uuid of the provider to delete
        """
        provider = KokuProvider(uuid=uuid)
        provider._delete(self.client)

    ##################################################
    # User Preferences
    ##################################################
    def path_user_preference(self, pref_uuid=None):
        """Return the endpoint for a user preference

        Arguments:
            pref_uuid - preference uuid of the endpoint
        """
        pref_path = '{}preferences/{}'.format(
            self.path(),
            '{}/'.format(pref_uuid) if pref_uuid else '')
        return pref_path

    def create_preference(self, name, preference, description=None):
        """Send POST request to create a user preference

        Arguments:
            name - Name of the preference to create
            preference - User preference (single item) dictionary containing
                a key=>value pair of the of user_preference=>value
                {'my-preference-name': 'my-preference-value'}
        """
        payload = {'name': name, 'preference': preference, 'description': description, }
        return self.client.post(self.path_user_preference(), payload=payload)

    def read_preference(self, pref_uuid=None):
        """Send GET request for user preference(s)
        Argument:
            preference_uuid -
                If None, return a list of all user preferences
                else a user preference
        """
        return self.client.get(self.path_user_preference(pref_uuid))

    def update_preference(self, pref_uuid, name=None, description=None, preference=None):
        """SEND PUT request to update a user preference"""
        payload = {}
        if name:
            payload['name'] = name

        if preference:
            payload['preference'] = preference

        if description:
            payload['description'] = description

        return self.client.put(self.path_user_preference(pref_uuid), payload=payload)

    def delete_preference(self, pref_uuid):
        """Send DELETE request to delete a user preference
        Argument:
            preference_uuid - uuid of the user preference to remove
        """
        return self.client.delete(self.path_user_preference(pref_uuid))


class KokuProvider(KokuObject):
    def __init__(self, client=None, uuid=None, name=None, provider_type="AWS", authentication=None, billing_source=None):
        """
        Arguments:
            client - Existing `hansei.api.client` object to use for authentication.
                This client authentication will determine what koku features client has access to
            uuid - UUID of an existing customer
            name - Name for the provider
            provider_type - Type of provider. Default is AWS
            authentication - Authentication for the provider
            billing_source - Billing source information for the provider
        """
        super().__init__(client=client, uuid=uuid)
        self.endpoint = KOKU_PROVIDER_PATH
        self.name = name
        self.provider_type = provider_type
        self.authentication = authentication
        self.billing_source = billing_source

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        payload = {
            'name': self.name,
            'type': self.provider_type,
            'authentication': self.authentication,
            'billing_source': self.billing_source,
        }

        return payload

    def load(self, payload):
        """Populate the object data from the response of a GET request

        Arguments:
            payload - dictionary object from json response
        """
        self.name = payload['name']
        self.provider_type = payload['type']
        self.authentication = payload['authentication']
        self.billing_source = payload['billing_source']
        self.uuid = payload['uuid']


class KokuBaseReport(object):
    """Base class for Koku reports"""
    def __init__(self, client):
        """
        Arguments:
            client - authenticated ``hansei.api.Client`` object used to issue api calls
        """
        self.client = client
        self.endpoint = None
        self.last_report = None

        # Initialize all properties storing all cached report data
        self._clear_report_cache()

    def get(self, report_filter=None, order_by=None, group_by=None):
        """
        Arguments:
            report_filter - Dictionary of filter queries key. Key:Value => Filter name:Filter Value
            order_by - tuple of the order by value.
                Example: ['cost', 'asc']
            group_by - List of tuples for accounts, services,... to group by
                Example: [['account', '*'], ['service', 'Compute Instance']]
        """

        query_params = {}
        if order_by:
            query_params['order_by[{}]'.format(order_by[0])] = order_by[1]

        if group_by:
            for group in group_by:
                key, val = group
                query_param_key = 'group_by[{}]'.format(key)
                # The key for group_by params can be duplicated so we need to set the query param
                # values to lists so that when we pass query_params and the payload to client.get
                # reponse.get() will know that we need to pass the key multiple times but with
                # different values
                if query_param_key not in query_params:
                    query_params[query_param_key] = []
                query_params[query_param_key].append(val)

        if report_filter:
            for key, val in report_filter.items():
                query_params['filter[{}]'.format(key)] = val

        # Clear the cache of items from the last report
        self._clear_report_cache()

        response = self.client.get(self.endpoint, params=query_params)
        self.last_report = response.json()

        return self.last_report

    @property
    def filter(self):
        """The filter params used in the last report query as returned by the Koku json response"""
        return self.last_report.get('filter') if self.last_report else None

    @property
    def order_by(self):
        """The order_by param used in the last report query as returned by the Koku json response"""
        return self.last_report.get('order_by') if self.last_report else None

    @property
    def group_by(self):
        """The group_by param used in the last report query as returned by the Koku json response"""
        return self.last_report.get('group_by') if self.last_report else None

    @property
    def data(self):
        return self.last_report.get('data') if self.last_report else None

    def _clear_report_cache(self):
        """ Clear all of the data that we cached during operations on the last report"""

        self._line_items = None

    def _traverse_report_line_items(self, root_object):
        """
        Recursively traverses the report data to generate a list of the cost
        or storage used per time_scope_unit
        """
        line_item_list = []

        root_object_type = type(root_object)
        if not root_object or (root_object_type not in [list, dict]):
            return line_item_list

        if root_object_type is list:
            for item in root_object:
                if type(item) in [list, dict]:
                    line_item_list.extend(self._traverse_report_line_items(item))
        else:
            if root_object_type is dict:
                # Once we hit 'values' key it will be a list that contains all
                # of the costs or storage usage for 'time_scope_units'
                if 'values' in root_object:
                    return line_item_list + root_object['values']

                for key, val in root_object.items():
                    if type(val) in [list, dict]:
                        line_item_list.extend(self._traverse_report_line_items(val))

        return line_item_list

    def report_line_items(self, data=None):
        """
        Returns a list of the 'total' value of an item fetched from the individual rows in the
        report.The item could be total cost/storage usage/VM uptime.

        Arguments:
            data (List OR dict)- data object as returned by a Koku report request
        """
        data = data or self.data

        if self._line_items:
            return self._line_items

        self._line_items = self._traverse_report_line_items(data)

        return self._line_items

    def calculate_total(self):
        """
        Calculates the total cost/storage usage/VM uptime by adding all of the individual
        items reported in report data.
        """
        # Check to see if we have a report saved
        if not self.data:
            return None

        total_item = decimal.Decimal(0.0)
        item_list = self.report_line_items(self.data)
        for item in item_list:
            total_item = total_item + (
                decimal.Decimal(item['total']) if item['total'] else 0.0)

        # Koku will return a null total if there are no line item charges in the list
        if len(item_list) == 0:
            total_item = None

        return total_item

    @property
    def total(self):
        """Returns the total json object of the report response"""
        return self.last_report.get('total') if self.last_report else None


class KokuCostReport(KokuBaseReport):
    """
    Class for interacting with the Koku Cost Reporting object as returned by
    the Koku json response.

    Cost report data generally takes the format of:
        data: [
            {
                date: YYYY-MM-DD
                values: [
                    {
                       date: DATE
                       units: CURRENCY
                       total: COST
                    }
                ]
            }
        ]
    """
    def __init__(self, client):
        super().__init__(client)
        self.endpoint = KOKU_COST_REPORTS_PATH


class KokuStorageReport(KokuBaseReport):
    """
    Class for interacting with the Koku Storage Reporting object as returned by
    the Koku json response.

    Storage inventory report data generally takes the format of:
        data": [
        {
            "date": "YYYY-MM-DD",
            "accounts": [
                {
                    "account": "XYZ",
                    "values": [
                        {
                            "date": "YYYY-MM-DD",
                            "units": STORAGE UNIT,
                            "account": "XYZ",
                            "total": STORAGE USAGE
                        }
                    ]
                },
            ]
        }]
    """
    def __init__(self, client):
        super().__init__(client)
        self.endpoint = KOKU_STORAGE_REPORTS_PATH


class KokuInstanceReport(KokuBaseReport):
    """
    Class for interacting with the Koku Instance Reporting object as returned by
    the Koku json response.

    Instance inventory report data generally takes the format of:
    "data": [
        {
            "date": "YYYY-MM-DD",
            "instance_types": [
                {
                    "instance_type": "AWS.INSTANCE_TYPE",
                    "values": [
                        {
                            "date": "YYYY-MM",
                            "units": "Hrs",
                            "instance_type": "AWS.INSTANCE_TYPE",
                            "total": XYZ.0,
                            "count": XYZ
                        }
                    ]
                },
            ]
        }]
    """
    def __init__(self, client):
        super().__init__(client)
        self.endpoint = KOKU_INSTANCE_REPORTS_PATH
