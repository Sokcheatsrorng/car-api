import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Car Selling API...")
    
    # Test registration
    print("\n1. Testing user registration...")
    register_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "password123",
        "full_name": "John Doe"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    print(f"Registration status: {response.status_code}")
    if response.status_code == 200:
        print(f"User created: {response.json()}")
    
    # Test login
    print("\n2. Testing user login...")
    login_data = {
        "username": "john_doe",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"Access token received: {access_token[:20]}...")
        
        # Headers for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test creating a car
        print("\n3. Testing car creation...")
        car_data = {
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "price": 25000.00,
            "mileage": 30000,
            "description": "Well maintained Toyota Camry in excellent condition",
            "color": "Silver",
            "fuel_type": "Gasoline",
            "transmission": "Automatic"
        }
        
        response = requests.post(f"{BASE_URL}/cars", json=car_data, headers=headers)
        print(f"Car creation status: {response.status_code}")
        if response.status_code == 200:
            car = response.json()
            car_id = car["id"]
            print(f"Car created: {car['make']} {car['model']} - ${car['price']}")
            
            # Test getting all cars
            print("\n4. Testing get all cars...")
            response = requests.get(f"{BASE_URL}/cars")
            print(f"Get cars status: {response.status_code}")
            if response.status_code == 200:
                cars = response.json()
                print(f"Found {len(cars)} cars")
            
            # Test getting user's cars
            print("\n5. Testing get my cars...")
            response = requests.get(f"{BASE_URL}/my-cars", headers=headers)
            print(f"Get my cars status: {response.status_code}")
            if response.status_code == 200:
                my_cars = response.json()
                print(f"User has {len(my_cars)} cars")
            
            # Test car search
            print("\n6. Testing car search...")
            response = requests.get(f"{BASE_URL}/cars/search/Toyota")
            print(f"Search status: {response.status_code}")
            if response.status_code == 200:
                search_results = response.json()
                print(f"Found {len(search_results)} Toyota cars")
            
            # Test updating a car
            print("\n7. Testing car update...")
            update_data = {
                "price": 24000.00,
                "description": "Price reduced! Well maintained Toyota Camry"
            }
            response = requests.put(f"{BASE_URL}/cars/{car_id}", json=update_data, headers=headers)
            print(f"Update status: {response.status_code}")
            if response.status_code == 200:
                updated_car = response.json()
                print(f"Car updated: New price ${updated_car['price']}")

if __name__ == "__main__":
    test_api()
