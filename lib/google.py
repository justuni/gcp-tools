#!/usr/bin/env python
"""Classes for calling Google APIs."""

# import modules
import httplib2
import io
import json
import logging

from apiclient import http as apihttp

# import discovery.build, errors
from googleapiclient.discovery import build
from googleapiclient import errors

# import GoogleCredentials
from oauth2client.client import GoogleCredentials

# enable logging
logging.basicConfig(filename='logs/debug.log', level=logging.DEBUG)


# Google Class
class Google(object):
    """Class with methods for working with Google APIs."""

    def __init__(self):
        """Initialize."""
        self.http = None

        self.billing = None
        self.compute = None
        self.compute_alpha = None
        self.crm = None
        self.iam = None
        self.smgt = None
        self.storage = None

    def auth(self):
        """Athenticate with gcloud application-default credentials."""
        # get application-default credentials from gcloud
        credentials = GoogleCredentials.get_application_default()
        self.http = credentials.authorize(httplib2.Http())

        #
        # build the various services that we'll need
        #

        # build a cloud billing API service
        self.billing = build('cloudbilling', 'v1', credentials=credentials)

        # build a compute API service
        self.compute = build('compute', 'v1', credentials=credentials)
        self.compute_alpha = build('compute', 'alpha', credentials=credentials)

        # build a cloud resource manager API service
        self.crm = build('cloudresourcemanager', 'v1', credentials=credentials)

        # build an iam API service
        self.iam = build('iam', 'v1', credentials=credentials)

        # build a service management API service
        self.smgt = build('servicemanagement', 'v1', credentials=credentials)

        # build a service management API service
        self.storage = build('storage', 'v1', credentials=credentials)

    def display_labels(self, labels):
        """Return a project's labels as a text string."""
        output = []
        for key in sorted(labels):
            value = labels[key]
            output.append('%s=%s' % (key, value))
        return ','.join(output)

    def display_parents(self, parent):
        """Return a project's org path as a text string."""
        output = []
        while parent:
            oid = parent['id']
            if parent['type'] == 'folder':
                org = self.get_folder(oid)
            elif parent['type'] == 'organization':
                org = self.get_organization('organizations/%s' % (oid))
                parent = None
            name = org['displayName']
            output.insert(0, name)

            if 'parent' in org:
                parent = {
                    'type': org['parent'].split('/')[0][0:-1],
                    'id': org['parent'].split('/')[1]
                }

        return ' > '.join(output)

    #
    # Cloud Billing API (cloudbilling)
    #
    def enable_project_billing(self, project_id, billing_account_name):
        """

        Function: enable_project_billing.

        Google Cloud Billing API - projects().updateBillingInfo()

        Parameters:

          project_id         - [type/description]
          billing_account_name - [type/description]

        Returns:

          return response
        """
        body = {
            'project_id': project_id,
            'billingAccountName': billing_account_name,
            'billingEnabled': True,
        }

        params = {
            'name': 'projects/%s' % project_id,
            'body': body,
        }

        return self.billing.projects().updateBillingInfo(**params).execute()

    def get_billing_accounts(self):
        """

        Function: get_billing_accounts.

        Google Cloud Billing API - billingAccounts().list()

        Returns:

          return list of billing accounts
        """
        # create a request to list billingAccounts
        billing_accounts = self.billing.billingAccounts()
        request = billing_accounts.list()

        # create a list to hold all the projects
        billing_accounts_list = []

        # page through the responses
        while request is not None:

            # execute the request
            response = request.execute()

            # add projects to the projects list
            if 'billingAccounts' in response:
                billing_accounts_list.extend(response['billingAccounts'])

            request = billing_accounts.list_next(request, response)

        return billing_accounts_list

    #
    # Compute
    #
    def get_compute_project(self, project_id):
        """

        Function: get_compute_project.

        description

        Parameters:

          project_id  - [type/description]

        Return:

          return description
        """
        return self.compute.projects().get(project=project_id).execute()

    def set_common_instance_metadata(self, project_id, metadata):
        """

        Function: set_common_intsance_metadata.

        description

        Parameters:

          project_id  - [type/description]
          metadata    - [type/description]

        Return:

          return description
        """
        params = {
            'project': project_id,
            'body': metadata,
        }
        projects = self.compute.projects()
        return projects.setCommonInstanceMetadata(**params).execute()

    def set_default_service_account(self, project_id, service_account):
        """

        Function: set_default_service_account.

        description

        Parameters:

          project_id  - [type/description]
          service_account - [type/description]

        Return:

          return description
        """
        params = {
            'project': project_id,
            'body': {
                'email': service_account,
            },
        }
        projects = self.compute_alpha.projects()
        return projects.setDefaultServiceAccount(**params).execute()

    def set_project_usage_export_bucket(self, project_id, bucket_name):
        """

        Function: set_project_usage_export_bucket.

        description

        Parameters:

          project_id  - [type/description]
          bucket_name - [type/description]

        Return:

          return description
        """
        body = {
            'bucketName': bucket_name,
            'reportNamePrefix': 'usage',
        }

        params = {
            'project': project_id,
            'body': body,
        }

        return self.compute.projects().setUsageExportBucket(**params).execute()

    #
    # Cloud Resource Manager (cloudresourcemanager)
    #
    def create_project(self, project):
        """Return a created project."""
        try:
            return self.crm.projects().create(body=project).execute()
        except errors.HttpError, httperror:
            error = json.loads(httperror.content)['error']
            print '[%s]' % error['message']
            return {}

    def get_folder(self, folder_id):
        """Return a folder."""
        # create a request to list organizations
        url = 'https://cloudresourcemanager.googleapis.com/v2alpha1/folders/'
        url += folder_id

        headers = {'ContentType': 'application/json'}

        (response, content) = self.http.request(
            url,
            headers=headers,
            method='GET'
        )
        return json.loads(content)

    def get_folders(self, parent):
        """Return a list of folders of a parent."""
        # create a request to list organizations
        url = 'https://cloudresourcemanager.googleapis.com/v2alpha1/folders'
        url += '?parent='+parent

        headers = {'ContentType': 'application/json'}

        (response, content) = self.http.request(
            url,
            headers=headers,
            method='GET'
        )

        json_content = json.loads(content)
        if 'folders' in json_content:
            return json_content['folders']
        else:
            return {}

    def get_organization(self, name):
        """Return an organization."""
        return self.crm.organizations().get(name=name).execute()

    def get_organizations(self):
        """Return a list of organizations."""
        # create a request to list organizations
        org_search = self.crm.organizations().search(body={})
        response = org_search.execute()

        if 'organizations' in response:
            return response['organizations']

        return []

    def get_project(self, project_id):
        """Return a project."""
        # create a request to list projects
        return self.crm.projects().get(projectId=project_id).execute()

    def get_projects(self):
        """

        Function: get_projects.

        description

        Returns:

          return description
        """
        # create a request to list projects
        request = self.crm.projects().list()

        # create a list to hold all the projects
        projects = []

        # page through the responses
        while request is not None:

            # execute the request
            response = request.execute()

            # add projects to the projects list
            if 'projects' in response:
                projects.extend(response['projects'])

            request = self.crm.projects().list_next(request, response)

        return projects

    def set_iam_policy(self, project_id, policy):
        """

        Function: set_iam_policy.

        description

        Parameters:

          project_id   - [type/description]
          policy       - [type/description]

        Returns:

          return description
        """
        params = {
            'resource': project_id,
            'body': {
                'policy': policy
            }
        }

        try:
            return self.crm.projects().setIamPolicy(**params).execute()
        except errors.HttpError, httperror:
            error = json.loads(httperror.content)['error']
            print '[%s]' % error['message']
            return {}

    def update_project(self, project_id, body):
        """Return an updated project resource."""
        params = {
            'projectId': project_id,
            'body': body,
        }
        projects_update = self.crm.projects().update(**params)
        try:
            return projects_update.execute()
        except errors.HttpError as httperror:
            error = json.loads(httperror.content)['error']
            print '[%s]' % error['message']
            return {}

    #
    # IAM (Identity and Access Management) API (iam)
    #
    def create_service_account(
            self,
            project_id,
            account_id,
            display_name=None
    ):
        """

        Function: create_service_account.

        description

        Parameters:

          project_id   - [type/description]
          account_d    - [type/description]
          display_name - [type/description]

        Returns:

          return description
        """
        # set displayName
        if not display_name:
            display_name = account_id

        params = {
            'name': 'projects/'+project_id,
            'body': {
                'accountId': account_id,
                'serviceAccount': {
                    'displayName': display_name,
                },
            },
        }

        iam_service_accounts = self.iam.projects().serviceAccounts()
        try:
            return iam_service_accounts.create(**params).execute()
        except errors.HttpError as httperror:
            error = json.loads(httperror.content)['error']
            print '[%s]' % error['message'].split('/')[-1]
            return {}

    #
    # Service Management API (servicemanagement)
    #
    def enable_project_service(self, project_id, service_name):
        """Return an enabled project service response."""
        body = {
            'consumerId': 'project:%s' % project_id
        }
        params = {
            'serviceName': service_name,
            'body': body,
        }
        return self.smgt.services().enable(**params).execute()

    def get_service_operation(self, operation):
        """Return an operation."""
        return self.smgt.operations().get(name=operation).execute()

    #
    # Storage API (storage)
    #
    def create_bucket(self, project, bucket):
        """Create a GCP bucket."""
        params = {
            'project': project,
            'body': {
                'name': bucket,
            },
        }
        return self.storage.buckets().insert(**params).execute()

    def get_bucket(self, bucket):
        """Get get GCP bucket."""
        return self.storage.buckets().get(bucket=bucket).execute()

    def get_bucket_object(self, bucket_name, object_name):
        """Get the content of an object from a GCP bucket."""
        params = {
            'bucket': bucket_name,
            'object': object_name,
        }

        # get the storage object media
        request = self.storage.objects().get_media(**params)

        # The BytesIO object may be replaced with any io.Base instance.
        media = io.BytesIO()

        # create downloader
        downloader = apihttp.MediaIoBaseDownload(
            media,
            request,
            chunksize=1024*1024
        )

        done = False
        while not done:
            status, done = downloader.next_chunk()

        return media
