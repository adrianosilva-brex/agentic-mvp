import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class DynamoDBConfig:
    """
    Simplified DynamoDB configuration for Trip Management System.
    
    This class handles:
    - Creating and configuring the single trips table
    - Setting up GSIs for optimized queries
    - Managing LocalStack vs AWS connections
    """
    
    def __init__(
        self, 
        region_name: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1"), 
        endpoint_url: Optional[str] = os.getenv("LOCALSTACK_ENDPOINT")
    ):
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        
        # Configure boto3 client and resource
        if endpoint_url:
            # LocalStack configuration
            self.dynamodb_client = boto3.client(
                'dynamodb',
                region_name=region_name,
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
            )
            self.dynamodb_resource = boto3.resource(
                'dynamodb',
                region_name=region_name,
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
            )
        else:
            # AWS production configuration
            self.dynamodb_client = boto3.client('dynamodb', region_name=region_name)
            self.dynamodb_resource = boto3.resource('dynamodb', region_name=region_name)
    
    def create_trips_table(self, table_name: str = 'trips') -> bool:
        """
        Create the simplified trips table with essential GSIs.
        
        Schema Design:
        - Primary Key: trip_id (string)
        - GSI1: traveler_id-start_date-index for user trip queries
        - GSI2: status-updated_at-index for status-based queries
        
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
                    }
                ]
            )
            
            # Wait for table to be created
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"✅ Table {table_name} created successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"ℹ️  Table {table_name} already exists")
                return True
            else:
                print(f"❌ Error creating table {table_name}: {e}")
                return False
    
    def delete_table(self, table_name: str = 'trips') -> bool:
        """
        Delete the trips table (useful for cleanup/testing).
        
        Args:
            table_name: Name of the table to delete
            
        Returns:
            bool: True if table deleted successfully, False otherwise
        """
        try:
            self.dynamodb_client.delete_table(TableName=table_name)
            
            waiter = self.dynamodb_client.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name)
            
            print(f"✅ Table {table_name} deleted successfully")
            return True
            
        except ClientError as e:
            print(f"❌ Error deleting table {table_name}: {e}")
            return False
    
    def list_tables(self) -> list:
        """
        List all DynamoDB tables.
        
        Returns:
            list: List of table names
        """
        try:
            response = self.dynamodb_client.list_tables()
            return response['TableNames']
        except ClientError as e:
            print(f"❌ Error listing tables: {e}")
            return []
    
    def get_table_info(self, table_name: str = 'trips') -> Optional[dict]:
        """
        Get detailed information about the trips table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Optional[dict]: Table description or None if error
        """
        try:
            response = self.dynamodb_client.describe_table(TableName=table_name)
            return response['Table']
        except ClientError as e:
            print(f"❌ Error getting table info for {table_name}: {e}")
            return None

if __name__ == "__main__":
    # Example usage for testing
    config = DynamoDBConfig()
    
    # List existing tables
    tables = config.list_tables()
    print(f"Existing tables: {tables}")
    
    # Create trips table
    success = config.create_trips_table()
    if success:
        print("🎉 Trips table setup complete!")
        
        # Show table info
        table_info = config.get_table_info()
        if table_info:
            print(f"Table status: {table_info['TableStatus']}")
            print(f"Item count: {table_info['ItemCount']}")
