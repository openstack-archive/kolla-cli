***********************
HOSTS API - Reference
***********************


.. warning::

    This hosts documentation is work in progress and may change in near future.


Hosts API
===============

.. _get_hosts_all:

GET /v1/hosts
##########################
Retrieve all hosts in the inventory.


Request/Response:
************************************

.. code-block:: none

    Request:

    GET /v1/hosts
    Headers:
        X-Auth-Token: {token_id}

    Response:

    HTTP/1.1 200 OK
    {
      "hosts":[
        {
          "hostname":{host_name1},
          "groups":[
            {group_name1},
            {group_name2},
            .....
          ],
         },
         .....
       ]
    }


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Successful request.                                                         |
+------+-----------------------------------------------------------------------------+
| 401  | Missing or Invalid X-Auth-Token. Authentication required.                   |
+------+-----------------------------------------------------------------------------+

.. _get_host:

GET /v1/hosts/{host_name}
##########################
Retrieve the host for the given host name.


Request/Response:
************************************

.. code-block:: none

    Request:

    GET /v1/hosts/{host_name}
    Headers:
        X-Auth-Token: {token_id}

    Response:

    HTTP/1.1 200 OK
    {
      "hostname":{host_name},
      "groups":[
        {group_name1},
        {group_name2},
      ],
      .....
    }


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Successful request.                                                         |
+------+-----------------------------------------------------------------------------+
| 401  | Missing or Invalid X-Auth-Token. Authentication required.                   |
+------+-----------------------------------------------------------------------------+
| 404  | Host does not exist in inventory                                            |
+------+-----------------------------------------------------------------------------+


.. _post_host:

POST /v1/hosts
##########################
Create new host.

This call is used to create a new host and add it to the inventory.

Request/Response (create or replace host):
**************************************

.. code-block:: none

    Request:

    POST /v1/hosts/{host_name}
    Headers:
        Content-Type: application/json
        X-Auth-Token: {token_id}

    {
      "hostname":{host_name},
      "groups": [
        {group_name1},
        {group_name2},
        .....
      ],
    }

    Response:

    HTTP/1.1 200 OK


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Successfully created host.                                                  |
+------+-----------------------------------------------------------------------------+
| 400  | Bad Request.                                                                |
+------+-----------------------------------------------------------------------------+
| 401  | Missing or Invalid X-Auth-Token. Authentication required.                   |
+------+-----------------------------------------------------------------------------+
| 404  | Group does not exist in inventory                                           |
+------+-----------------------------------------------------------------------------+
| 409  | Host already exists in inventory                                            |
+------+-----------------------------------------------------------------------------+


.. _delete_host:

DELETE /v1/hosts/{host_name}
##############################

Delete host from the inventory.

Request/Response:
*****************

.. code-block:: none

    DELETE /v1/host/{host_name}
    Headers:
        X-Auth-Token: {token_id}

    Response:
    HTTP/1.1 200 OK


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Successfully deleted host.                                                  |
+------+-----------------------------------------------------------------------------+
| 401  | Missing or Invalid X-Auth-Token. Authentication required.                   |
+------+-----------------------------------------------------------------------------+

.. _check_host:

POST /v1/hosts/{host_name}/actions
##############################

Check verifies that the host has its ssh keys set up correctly (can be accessed without a
password from the deploy host). If the host check failed, the reason will be provided in
the response message.

Request/Response:
*****************

.. code-block:: none

    POST /v1/hosts/{host_name}/actions
    Headers:
        Content-Type: application/json
        X-Auth-Token: {token_id}
                {
                  "check": {
                     "host-name": {host_name},
                  }
                }

Response:
*********

.. code-block:: none

    200 OK

    {
        "message":{message_string}
    }


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Host check was successful                                                   |
+------+-----------------------------------------------------------------------------+
| 400  | Bad Request                                                                 |
+------+-----------------------------------------------------------------------------+
| 401  | Invalid X-Auth-Token or the token doesn't have permissions to this resource |
+------+-----------------------------------------------------------------------------+
| 404  | Host does not exist in inventory                                            |
+------+-----------------------------------------------------------------------------+
| 405  | Host check failed                                                           |
+------+-----------------------------------------------------------------------------+

.. _setup_host:

POST /v1/hosts/actions
##############################

Host setup distributes the ssh keys into the appropriate directory/file on the host.
This assumes docker has been installed and is running on the host. Setup can be done
for a single host or multiple hosts.

If a single host is to be setup, the host-name and host-password attributes must be
supplied. If multiple hosts are to be setup, the hosts-file-path must be
supplied.

Either the host-name/password or hosts-file-path must be supplied. If both are supplied,
then all the hosts specified will be setup.

If the host setup failed, the reason will be provided in
the response message.

Request/Response:
*****************

.. code-block:: none

    POST /v1/hosts/actions
    Headers:
        Content-Type: application/json
        X-Auth-Token:      {token_id}

        {
          "setup": {
            "host-name": {host_name},
            "host-password": {password},
            "hosts-file-path": {hosts_file_path}
          }
        }

Response:
*********

.. code-block:: none

    200 OK

    {
        "message":{message_string}
    }


HTTP Status Codes
*****************

+------+-----------------------------------------------------------------------------+
| Code | Description                                                                 |
+======+=============================================================================+
| 200  | Host setup was successful                                                   |
+------+-----------------------------------------------------------------------------+
| 400  | Bad Request                                                                 |
+------+-----------------------------------------------------------------------------+
| 401  | Invalid X-Auth-Token or the token doesn't have permissions to this resource |
+------+-----------------------------------------------------------------------------+
| 404  | Host does not exist in inventory                                            |
+------+-----------------------------------------------------------------------------+
| 405  | Host setup failed                                                           |
+------+-----------------------------------------------------------------------------+

