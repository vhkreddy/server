import boto3
from botocore.errorfactory import ClientError
import os
import pandas as pd
from django.conf import settings

class AWSConnect:
    def __init__(self):
        self.access_key = settings.A_KEY
        self.secret_key = settings.S_KEY
        self.bucket = settings.S3_BUCKET
        self.s3client = boto3.client('s3', 
            aws_access_key_id = self.access_key,
            aws_secret_access_key = self.secret_key
        )
        self.session = boto3.session.Session(aws_access_key_id=self.access_key,
                                    aws_secret_access_key=self.secret_key)
        
        self.s3resource = boto3.resource('s3',
            aws_access_key_id = self.access_key,
            aws_secret_access_key = self.secret_key                      
        )
        self.BUCKET = self.s3resource.Bucket(self.bucket)
        
    def download_dir(self, prefix, local):
        """
        params:
        - prefix: pattern to match in s3
        - local: local path to folder in which to place files
        """
        client = self.s3client
        bucket = self.bucket
        keys = []
        dirs = []
        next_token = ''
        base_kwargs = {
            'Bucket':bucket,
            'Prefix':prefix,
        }
        while next_token is not None:
            kwargs = base_kwargs.copy()
            if next_token != '':
                kwargs.update({'ContinuationToken': next_token})
            results = client.list_objects_v2(**kwargs)
            contents = results.get('Contents')
            for i in contents:
                k = i.get('Key')
                if k[-1] != '/':
                    keys.append(k)
                else:
                    dirs.append(k)
            next_token = results.get('NextContinuationToken')
        for d in dirs:
            dest_pathname = os.path.join(local, d)
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
        for k in keys:
            dest_pathname = os.path.join(local, k)
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            client.download_file(bucket, k, dest_pathname)
    
    def getKey(self, key):
        return self.s3client.get_object(Bucket=self.bucket,Key=key) 
    
    def downloadFilesInFolder(self,source_path, destination_path):
        """
        params:
        - source_path: it can be folder path or file prefix (folder prefix wont work)
        This should end with a '/'
        - destination_path: destination path to be downloaded
        notes:
        - This will download files at single level nested folders dont work
        """
        if not os.path.exists(os.path.dirname(destination_path)):
            os.makedirs(os.path.dirname(destination_path))
        objs = self.BUCKET.objects.filter(Prefix = source_path, Delimiter='/')
        for obj in objs:
            key = obj.key
            path, filename = os.path.split(key)
            if key[-1] == "/" or os.path.exists(destination_path+filename):
                continue
            self.BUCKET.download_file(key, destination_path+filename)

    def list_objects(self, delimiter):
        return self.s3client.list_objects(Bucket= self.bucket, Delimiter=delimiter)

    def getKeys(self):
        result = self.s3client.list_objects(Bucket=self.bucket,Prefix='KNV/excel_files/')
        for obj in result.Contents:
            print(obj)
    
    def isKeyPresent(self, key):
        try:
            self.s3client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
        # objs = list(self.BUCKET.objects.filter(Prefix=key))
        # if len(objs) > 0 and objs[0].key == key:
        #     return True
        # else:
        #     return False