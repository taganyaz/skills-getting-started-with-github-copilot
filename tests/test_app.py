"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original participants
    original_participants = {
        name: list(activity["participants"]) 
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original participants after test
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that get activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_already_registered(self, client):
        """Test signup when student is already registered returns 400"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "teststudent@mergington.edu"
        
        # Verify student is not in the activity
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up
        client.post("/activities/Chess Club/signup", params={"email": email})
        
        # Verify student is now in the activity
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # michael@mergington.edu is already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant from the activity"""
        email = "michael@mergington.edu"
        
        # Verify student is in the activity
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete("/activities/Chess Club/unregister", params={"email": email})
        
        # Verify student is no longer in the activity
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
