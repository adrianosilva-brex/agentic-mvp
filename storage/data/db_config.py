import boto3
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError

load_dotenv()

class DynamoDBConfig:
    """
    DynamoDB configuration and setup for the Trip Management System.
    
    This class handles:
    - Creating and configuring DynamoDB tables
    - Setting up indexes for optimized queries
    - Managing table schemas based on MVP requirements
    """
    
    def __init__(
        self, 
        region_name: str = os.getenv("AWS_DEFAULT_REGION"), 
        endpoint_url: Optional[str] = os.getenv("LOCALSTACK_ENDPOINT")
    ):
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        
        if endpoint_url:
            self.dynamodb_client = boto3.client(
                'dynamodb',
                region_name=region_name,
                endpoint_url=endpoint_url
            )
            self.dynamodb_resource = boto3.resource(
                'dynamodb',
                region_name=region_name,
                endpoint_url=endpoint_url
            )
        else:
            # For AWS production
            self.dynamodb_client = boto3.client('dynamodb', region_name=region_name)
            self.dynamodb_resource = boto3.resource('dynamodb', region_name=region_name)
    
    def create_trips_table(self, table_name: str = 'trips') -> bool:
        """
        Create the main trips table with flexible schema support.
        
        Schema Design:
        - Partition Key: trip_id (string)
        - Attributes: Flexible JSON document with version tracking
        - GSI1: traveler_id-start_date-index for user queries
        - GSI2: status-updated_at-index for status-based queries
        - GSI3: origin_type-trip_confidence-index for merge candidate queries
        
        Args:
            table_name: Name of the trips table
            
        Returns:
            bool: True if table created successfully, False otherwise
        """
        try:
            table = self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'trip_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'trip_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'traveler_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'start_date',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'status',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'updated_at',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'origin_type',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'trip_confidence',
                        'AttributeType': 'N'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'traveler_id-start_date-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'traveler_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'start_date',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'status-updated_at-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'status',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'updated_at',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'origin_type-trip_confidence-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'origin_type',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'trip_confidence',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"Table {table_name} created successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {table_name} already exists")
                return True
            else:
                print(f"Error creating table {table_name}: {e}")
                return False
    
    def create_documents_metadata_table(self, table_name: str = 'documents_metadata') -> bool:
        """
        Create the documents metadata table for S3 document tracking.
        
        Schema Design:
        - Partition Key: document_id (string)
        - GSI1: source_type-upload_timestamp-index for document type queries
        - GSI2: processing_status-upload_timestamp-index for processing status queries
        
        Args:
            table_name: Name of the documents metadata table
            
        Returns:
            bool: True if table created successfully, False otherwise
        """
        try:
            table = self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'document_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'document_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'source_type',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'upload_timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'processing_status',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'source_type-upload_timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'source_type',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'upload_timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'processing_status-upload_timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'processing_status',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'upload_timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ]
            )
            
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"Table {table_name} created successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {table_name} already exists")
                return True
            else:
                print(f"Error creating table {table_name}: {e}")
                return False
    
    def create_field_registry_table(self, table_name: str = 'field_registry') -> bool:
        """
        Create the field registry table for tracking observed fields.
        
        Schema Design:
        - Partition Key: field_id (string)
        - GSI1: source_namespace-occurrence_count-index for namespace queries
        - GSI2: data_type-first_seen-index for type-based queries
        
        Args:
            table_name: Name of the field registry table
            
        Returns:
            bool: True if table created successfully, False otherwise
        """
        try:
            table = self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'field_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'field_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'source_namespace',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'occurrence_count',
                        'AttributeType': 'N'
                    },
                    {
                        'AttributeName': 'data_type',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'first_seen',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'source_namespace-occurrence_count-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'source_namespace',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'occurrence_count',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'data_type-first_seen-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'data_type',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'first_seen',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ]
            )
            
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"Table {table_name} created successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {table_name} already exists")
                return True
            else:
                print(f"Error creating table {table_name}: {e}")
                return False
    
    def setup_all_tables(self) -> bool:
        """
        Create all required tables for the Trip Management System.
        
        Returns:
            bool: True if all tables created successfully, False otherwise
        """
        print("Setting up DynamoDB tables for Trip Management System...")
        
        results = [
            self.create_trips_table(),
            self.create_documents_metadata_table(),
            self.create_field_registry_table()
        ]
        
        if all(results):
            print("All tables created successfully!")
            return True
        else:
            print("Some tables failed to create")
            return False
    
    def delete_table(self, table_name: str) -> bool:
        """
        Delete a DynamoDB table (useful for cleanup/testing).
        
        Args:
            table_name: Name of the table to delete
            
        Returns:
            bool: True if table deleted successfully, False otherwise
        """
        try:
            self.dynamodb_client.delete_table(TableName=table_name)
            
            waiter = self.dynamodb_client.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
            
            print(f"Table {table_name} deleted successfully")
            return True
            
        except ClientError as e:
            print(f"Error deleting table {table_name}: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """
        List all DynamoDB tables.
        
        Returns:
            List[str]: List of table names
        """
        try:
            response = self.dynamodb_client.list_tables()
            return response['TableNames']
        except ClientError as e:
            print(f"Error listing tables: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Optional[Dict]: Table description or None if error
        """
        try:
            response = self.dynamodb_client.describe_table(TableName=table_name)
            return response['Table']
        except ClientError as e:
            print(f"Error getting table info for {table_name}: {e}")
            return None

# Helper functions for DynamoDB data type conversion
class DynamoDBHelper:
    """Helper class for DynamoDB data type conversions and utilities."""
    
    @staticmethod
    def decimal_to_float(obj):
        """
        Convert Decimal objects to float for JSON serialization.
        
        Args:
            obj: Object that may contain Decimal values
            
        Returns:
            Object with Decimals converted to floats
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: DynamoDBHelper.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper.decimal_to_float(item) for item in obj]
        return obj
    
    @staticmethod
    def float_to_decimal(obj):
        """
        Convert float objects to Decimal for DynamoDB storage.
        
        Args:
            obj: Object that may contain float values
            
        Returns:
            Object with floats converted to Decimals
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: DynamoDBHelper.float_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper.float_to_decimal(item) for item in obj]
        return obj
    
    @staticmethod
    def current_timestamp() -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.utcnow().isoformat() + 'Z'

if __name__ == "__main__":
    # Example usage for LocalStack development
    config = DynamoDBConfig(
        region_name='us-east-1',
        endpoint_url='http://localhost:4566'  # LocalStack endpoint
    )
    
    # Setup all tables
    config.setup_all_tables()
    
    # List tables to verify creation
    tables = config.list_tables()
    print(f"Created tables: {tables}")