"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    })
    yield


class TestRoot:
    """Tests for root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all(self, client):
        """Test that get_activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants(self, client):
        """Test that participants are returned correctly"""
        response = client.get("/activities")
        data = response.json()
        
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
        assert data["Programming Class"]["participants"] == ["emma@mergington.edu", "sophia@mergington.edu"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student(self, client):
        """Test signing up a new student"""
        response = client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signups are rejected"""
        # Try to sign up a student who's already registered
        response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post("/activities/NonExistent%20Activity/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_adds_participant(self, client):
        """Test that signup properly adds participant to list"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Programming Class"]["participants"])
        
        client.post("/activities/Programming%20Class/signup?email=newstudent@mergington.edu")
        
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Programming Class"]["participants"])
        
        assert updated_count == initial_count + 1


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.post("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant not in the activity"""
        response = client.post("/activities/Chess%20Club/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.post("/activities/NonExistent%20Activity/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_removes_participant(self, client):
        """Test that unregister properly removes participant from list"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        client.post("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
        
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count - 1


class TestSignupAndUnregister:
    """Integration tests for signup and unregister"""

    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "teststudent@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Gym%20Class/signup?email={email}")
        response = client.get("/activities")
        assert email in response.json()["Gym Class"]["participants"]
        
        # Unregister
        client.post(f"/activities/Gym%20Class/unregister?email={email}")
        response = client.get("/activities")
        assert email not in response.json()["Gym Class"]["participants"]

    def test_signup_multiple_students(self, client):
        """Test signing up multiple different students"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/Gym%20Class/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        
        for email in emails:
            assert email in participants
