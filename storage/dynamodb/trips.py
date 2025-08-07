import boto3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
from botocore.exceptions import ClientError
from db_config import DynamoDBConfig

class TripsService:
    """
    Trip management operations for the simplified DynamoDB schema.
    
    Handles all CRUD operations for trips including:
    - Creating trips (explicit and auto-generated)
    - Reading trips (by ID, user, status)
    - Updating trips with version management
    - Deleting trips
    - Querying with GSIs
    """
    
    def __init__(self, config:  DynamoDBConfig = None, table_name: str = 'trips'):
        self.config = config or DynamoDBConfig()
        self.table_name = table_name
        self.table = self.config.dynamodb_resource.Table(table_name)
    
    def _current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        return obj
    
    def _prepare_for_dynamodb(self, obj: Any) -> Any:
        """Convert float objects to Decimal for DynamoDB storage."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._prepare_for_dynamodb(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_dynamodb(item) for item in obj]
        return obj
    
    def create_trip(self, trip_data: Dict[str, Any]) -> bool:
        """
        Create a new trip.
        
        Args:
            trip_data: Trip data dictionary following the simplified schema
            
        Returns:
            bool: True if trip created successfully
        """
        try:
            # Ensure required fields
            if 'trip_id' not in trip_data:
                raise ValueError("trip_id is required")
            
            # Set default values for required fields
            current_time = self._current_timestamp()
            trip_data.setdefault('version', 1)
            trip_data.setdefault('updated_at', current_time)
            trip_data.setdefault('status', 'confirmed')
            trip_data.setdefault('origin_type', 'explicit')
            trip_data.setdefault('trip_confidence', 1.0)
            
            # Initialize version history
            if 'version_history' not in trip_data:
                trip_data['version_history'] = [
                    {
                        'version': 1,
                        'timestamp': current_time,
                        'changes': ['trip created'],
                        'source': trip_data.get('source', 'manual')
                    }
                ]
            
            # Convert floats to Decimals for DynamoDB
            prepared_data = self._prepare_for_dynamodb(trip_data)
            
            # Put item in DynamoDB
            self.table.put_item(Item=prepared_data)
            print(f"✅ Trip {trip_data['trip_id']} created successfully")
            return True
            
        except ClientError as e:
            print(f"❌ Error creating trip: {e}")
            return False
        except Exception as e:
            print(f"❌ Error creating trip: {e}")
            return False
    
    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a trip by ID.
        
        Args:
            trip_id: The trip ID
            
        Returns:
            Optional[Dict]: Trip data or None if not found
        """
        try:
            response = self.table.get_item(Key={'trip_id': trip_id})
            
            if 'Item' in response:
                return self._convert_decimals(response['Item'])
            else:
                print(f"⚠️  Trip {trip_id} not found")
                return None
                
        except ClientError as e:
            print(f"❌ Error getting trip {trip_id}: {e}")
            return None
    
    def update_trip(self, trip_id: str, updates: Dict[str, Any], change_reason: str = "Manual update") -> bool:
        """
        Update a trip with version management.
        
        Args:
            trip_id: The trip ID
            updates: Dictionary of fields to update
            change_reason: Reason for the change
            
        Returns:
            bool: True if trip updated successfully
        """
        try:
            # Get current trip to manage version
            current_trip = self.get_trip(trip_id)
            if not current_trip:
                print(f"❌ Cannot update trip {trip_id}: not found")
                return False
            
            # Prepare update
            current_version = current_trip.get('version', 1)
            new_version = current_version + 1
            current_time = self._current_timestamp()
            
            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            # Add version and timestamp updates
            update_expression_parts.append("#version = :new_version")
            update_expression_parts.append("updated_at = :timestamp")
            expression_attribute_names["#version"] = "version"
            expression_attribute_values[":new_version"] = new_version
            expression_attribute_values[":timestamp"] = current_time
            
            # Add field updates
            change_list = []
            for field, value in updates.items():
                if field in ['trip_id', 'version', 'updated_at']:
                    continue  # Skip protected fields
                
                # Handle nested updates
                if '.' in field:
                    # For nested fields like "southwest_booking.departure.time"
                    parts = field.split('.')
                    expr = ""
                    for i, part in enumerate(parts):
                        attr_name = f"#attr{i}"
                        expression_attribute_names[attr_name] = part
                        if i == 0:
                            expr = attr_name
                        else:
                            expr += f".{attr_name}"
                    
                    update_expression_parts.append(f"{expr} = :val_{field.replace('.', '_')}")
                    expression_attribute_values[f":val_{field.replace('.', '_')}"] = self._prepare_for_dynamodb(value)
                else:
                    # Simple field update
                    attr_name = f"#attr_{field}"
                    expression_attribute_names[attr_name] = field
                    update_expression_parts.append(f"{attr_name} = :val_{field}")
                    expression_attribute_values[f":val_{field}"] = self._prepare_for_dynamodb(value)
                
                change_list.append(f"{field} updated")
            
            # Add version history entry
            version_entry = {
                'version': new_version,
                'timestamp': current_time,
                'changes': change_list,
                'source': change_reason
            }
            
            update_expression_parts.append("version_history = list_append(version_history, :version_entry)")
            expression_attribute_values[":version_entry"] = [version_entry]
            
            # Execute update
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            self.table.update_item(
                Key={'trip_id': trip_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            print(f"✅ Trip {trip_id} updated to version {new_version}")
            return True
            
        except ClientError as e:
            print(f"❌ Error updating trip {trip_id}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error updating trip {trip_id}: {e}")
            return False
    
    def delete_trip(self, trip_id: str) -> bool:
        """
        Delete a trip.
        
        Args:
            trip_id: The trip ID
            
        Returns:
            bool: True if trip deleted successfully
        """
        try:
            self.table.delete_item(Key={'trip_id': trip_id})
            print(f"✅ Trip {trip_id} deleted successfully")
            return True
            
        except ClientError as e:
            print(f"❌ Error deleting trip {trip_id}: {e}")
            return False
    
    def get_user_trips(self, traveler_id: str, start_date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all trips for a user, optionally filtered by start date.
        
        Args:
            traveler_id: The traveler ID
            start_date_filter: Optional start date filter (ISO format)
            
        Returns:
            List[Dict]: List of trips
        """
        try:
            if start_date_filter:
                response = self.table.query(
                    IndexName='traveler_id-start_date-index',
                    KeyConditionExpression='traveler_id = :traveler_id AND start_date >= :start_date',
                    ExpressionAttributeValues={
                        ':traveler_id': traveler_id,
                        ':start_date': start_date_filter
                    }
                )
            else:
                response = self.table.query(
                    IndexName='traveler_id-start_date-index',
                    KeyConditionExpression='traveler_id = :traveler_id',
                    ExpressionAttributeValues={
                        ':traveler_id': traveler_id
                    }
                )
            
            return [self._convert_decimals(item) for item in response['Items']]
            
        except ClientError as e:
            print(f"❌ Error getting trips for user {traveler_id}: {e}")
            return []
    
    def get_trips_by_status(self, status: str, updated_since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trips by status, optionally filtered by update time.
        
        Args:
            status: Trip status (confirmed, tentative, cancelled)
            updated_since: Optional timestamp filter (ISO format)
            
        Returns:
            List[Dict]: List of trips
        """
        try:
            if updated_since:
                response = self.table.query(
                    IndexName='status-updated_at-index',
                    KeyConditionExpression='#status = :status AND updated_at >= :updated_since',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': status,
                        ':updated_since': updated_since
                    }
                )
            else:
                response = self.table.query(
                    IndexName='status-updated_at-index',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': status
                    }
                )
            
            return [self._convert_decimals(item) for item in response['Items']]
            
        except ClientError as e:
            print(f"❌ Error getting trips by status {status}: {e}")
            return []
    
    def find_merge_candidates(self, traveler_id: str, confidence_threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        Find auto-generated trips that might need merging.
        
        Args:
            traveler_id: The traveler ID
            confidence_threshold: Maximum confidence score to consider for merging
            
        Returns:
            List[Dict]: List of potential merge candidate trips
        """
        try:
            response = self.table.scan(
                FilterExpression='traveler_id = :traveler_id AND origin_type = :origin_type AND trip_confidence < :confidence',
                ExpressionAttributeValues={
                    ':traveler_id': traveler_id,
                    ':origin_type': 'derived',
                    ':confidence': Decimal(str(confidence_threshold))
                }
            )
            
            return [self._convert_decimals(item) for item in response['Items']]
            
        except ClientError as e:
            print(f"❌ Error finding merge candidates: {e}")
            return []
    
    def list_all_trips(self) -> List[Dict[str, Any]]:
        """
        List all trips (for development/testing purposes).
        
        Returns:
            List[Dict]: List of all trips
        """
        try:
            response = self.table.scan()
            return [self._convert_decimals(item) for item in response['Items']]
            
        except ClientError as e:
            print(f"❌ Error listing all trips: {e}")
            return []

if __name__ == "__main__":
    # Example usage
    trips_service = TripsService()
    
    # Test basic operations
    print("🧪 Testing trips operations...")
    
    # List all trips
    all_trips = trips_service.list_all_trips()
    print(f"Current trips count: {len(all_trips)}")