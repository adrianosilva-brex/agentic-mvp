"""
SQLite database setup for weather and location data
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random


class WeatherDatabase:
    """SQLite database for weather and location information."""
    
    def __init__(self, db_path="weather_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database with tables and sample data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            state TEXT,
            latitude REAL,
            longitude REAL,
            population INTEGER,
            timezone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER,
            date DATE,
            temperature_celsius REAL,
            temperature_fahrenheit REAL,
            humidity INTEGER,
            precipitation_mm REAL,
            wind_speed_kmh REAL,
            condition TEXT,
            pressure_hpa REAL,
            visibility_km REAL,
            uv_index INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES cities (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS travel_destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER,
            category TEXT,
            attraction_name TEXT,
            description TEXT,
            rating REAL,
            cost_level TEXT,
            best_season TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES cities (id)
        )
        ''')
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM cities")
        if cursor.fetchone()[0] == 0:
            self._populate_sample_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _populate_sample_data(self, cursor):
        """Populate database with sample data."""
        
        # Sample cities
        cities_data = [
            ("Tokyo", "Japan", None, 35.6762, 139.6503, 37400068, "Asia/Tokyo"),
            ("New York", "United States", "New York", 40.7128, -74.0060, 8336817, "America/New_York"),
            ("London", "United Kingdom", "England", 51.5074, -0.1278, 9648110, "Europe/London"),
            ("Paris", "France", None, 48.8566, 2.3522, 2165423, "Europe/Paris"),
            ("Sydney", "Australia", "New South Wales", -33.8688, 151.2093, 5312163, "Australia/Sydney"),
            ("São Paulo", "Brazil", None, -23.5505, -46.6333, 12325232, "America/Sao_Paulo"),
            ("Mumbai", "India", "Maharashtra", 19.0760, 72.8777, 20411274, "Asia/Kolkata"),
            ("Dubai", "United Arab Emirates", None, 25.2048, 55.2708, 3331420, "Asia/Dubai"),
            ("Singapore", "Singapore", None, 1.3521, 103.8198, 5685807, "Asia/Singapore"),
            ("Barcelona", "Spain", "Catalonia", 41.3851, 2.1734, 1620343, "Europe/Madrid"),
            ("Amsterdam", "Netherlands", "North Holland", 52.3676, 4.9041, 872757, "Europe/Amsterdam"),
            ("Bangkok", "Thailand", None, 13.7563, 100.5018, 10539415, "Asia/Bangkok"),
            ("Cairo", "Egypt", None, 30.0444, 31.2357, 20900604, "Africa/Cairo"),
            ("Mexico City", "Mexico", None, 19.4326, -99.1332, 21581093, "America/Mexico_City"),
            ("Istanbul", "Turkey", None, 41.0082, 28.9784, 15462452, "Europe/Istanbul")
        ]
        
        cursor.executemany('''
        INSERT INTO cities (name, country, state, latitude, longitude, population, timezone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', cities_data)
        
        # Generate weather data for the last 30 days for each city
        cursor.execute("SELECT id, name, latitude FROM cities")
        cities = cursor.fetchall()
        
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Foggy", "Snowy"]
        
        for city_id, city_name, latitude in cities:
            for days_ago in range(30):
                date = datetime.now() - timedelta(days=days_ago)
                
                # Base temperature on latitude (rough approximation)
                base_temp = 25 - abs(latitude) * 0.5 + random.uniform(-8, 8)
                temp_c = round(base_temp, 1)
                temp_f = round(temp_c * 9/5 + 32, 1)
                
                humidity = random.randint(30, 90)
                precipitation = round(random.uniform(0, 20) if random.random() > 0.7 else 0, 1)
                wind_speed = round(random.uniform(5, 35), 1)
                condition = random.choice(weather_conditions)
                pressure = round(random.uniform(980, 1030), 1)
                visibility = round(random.uniform(5, 25), 1)
                uv_index = random.randint(1, 11)
                
                cursor.execute('''
                INSERT INTO weather_data 
                (city_id, date, temperature_celsius, temperature_fahrenheit, humidity, 
                 precipitation_mm, wind_speed_kmh, condition, pressure_hpa, visibility_km, uv_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (city_id, date.date(), temp_c, temp_f, humidity, precipitation, 
                      wind_speed, condition, pressure, visibility, uv_index))
        
        # Add travel destinations
        destinations_data = [
            (1, "Historical", "Tokyo Imperial Palace", "Historic palace complex in central Tokyo", 4.2, "Free", "Spring/Fall"),
            (1, "Cultural", "Senso-ji Temple", "Ancient Buddhist temple in Asakusa", 4.5, "Free", "Year-round"),
            (1, "Entertainment", "Tokyo Disneyland", "Famous theme park", 4.3, "Expensive", "Year-round"),
            (2, "Landmark", "Statue of Liberty", "Iconic American symbol", 4.4, "Moderate", "Spring/Summer"),
            (2, "Cultural", "Metropolitan Museum", "World-renowned art museum", 4.6, "Moderate", "Year-round"),
            (2, "Entertainment", "Broadway Shows", "World-famous theater district", 4.7, "Expensive", "Year-round"),
            (3, "Historical", "Tower of London", "Historic castle and Crown Jewels", 4.3, "Moderate", "Year-round"),
            (3, "Cultural", "British Museum", "World history and culture", 4.5, "Free", "Year-round"),
            (3, "Landmark", "Big Ben", "Iconic clock tower", 4.2, "Free", "Year-round"),
            (4, "Landmark", "Eiffel Tower", "Iconic iron tower", 4.4, "Moderate", "Year-round"),
            (4, "Cultural", "Louvre Museum", "World's largest art museum", 4.6, "Moderate", "Year-round"),
            (4, "Historical", "Notre-Dame Cathedral", "Gothic cathedral", 4.3, "Free", "Year-round"),
            (5, "Landmark", "Sydney Opera House", "Architectural masterpiece", 4.5, "Moderate", "Year-round"),
            (5, "Natural", "Bondi Beach", "Famous beach", 4.2, "Free", "Summer"),
            (5, "Cultural", "Art Gallery of NSW", "Premier art collection", 4.1, "Free", "Year-round")
        ]
        
        cursor.executemany('''
        INSERT INTO travel_destinations 
        (city_id, category, attraction_name, description, rating, cost_level, best_season)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', destinations_data)
    
    def execute_query(self, query, params=None):
        """Execute a SQL query and return results."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            # Convert to list of dictionaries
            return [dict(row) for row in results]
        
        except Exception as e:
            raise Exception(f"Database query error: {str(e)}")
        finally:
            conn.close()
    
    def get_schema_info(self):
        """Get database schema information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        schema_info = {}
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema_info[table_name] = {
                "columns": [{"name": col[1], "type": col[2], "nullable": not col[3]} for col in columns],
                "sample_query": f"SELECT * FROM {table_name} LIMIT 3"
            }
        
        conn.close()
        return schema_info


def main():
    """Test the database setup."""
    print("🗄️  Setting up Weather Database...")
    
    db = WeatherDatabase()
    
    print("📊 Schema Information:")
    schema = db.get_schema_info()
    for table_name, info in schema.items():
        print(f"\n📋 Table: {table_name}")
        for col in info["columns"]:
            print(f"   - {col['name']} ({col['type']})")
    
    print("\n🔍 Sample Queries:")
    
    # Test query 1: Recent weather in Tokyo
    print("\n1. Recent weather in Tokyo:")
    results = db.execute_query("""
        SELECT c.name, w.date, w.temperature_celsius, w.condition, w.humidity
        FROM cities c 
        JOIN weather_data w ON c.id = w.city_id 
        WHERE c.name = 'Tokyo' 
        ORDER BY w.date DESC 
        LIMIT 5
    """)
    for row in results:
        print(f"   {row['date']}: {row['temperature_celsius']}°C, {row['condition']}, {row['humidity']}% humidity")
    
    # Test query 2: Attractions in Paris
    print("\n2. Attractions in Paris:")
    results = db.execute_query("""
        SELECT c.name, td.attraction_name, td.category, td.rating
        FROM cities c 
        JOIN travel_destinations td ON c.id = td.city_id 
        WHERE c.name = 'Paris'
    """)
    for row in results:
        print(f"   {row['attraction_name']} ({row['category']}) - {row['rating']}★")
    
    print("\n✅ Database setup complete!")


if __name__ == "__main__":
    main()