"""Tests for the High School Management System API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    # Store original participants
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    # Restore original participants after test
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Soccer Team" in data
        assert "Basketball Team" in data
        assert "Art Club" in data
        assert "Programming Class" in data

    def test_get_activities_contains_required_fields(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to the activity"""
        email = "teststudent@mergington.edu"
        response = client.post(f"/activities/Art Club/signup?email={email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Art Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test that duplicate signup returns 400"""
        # First signup
        response = client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        assert response.status_code == 200
        # Second signup with same email
        response = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_activity_full(self, client):
        """Test that signup returns error when activity is full"""
        # Fill up Chess Club (max 12 participants)
        # First remove existing participants to have a clean slate
        activities["Chess Club"]["participants"] = []
        
        # Add 12 participants to fill the activity
        for i in range(12):
            response = client.post(f"/activities/Chess Club/signup?email=student{i}@mergington.edu")
            assert response.status_code == 200
        
        # Try to add 13th participant
        response = client.post("/activities/Chess Club/signup?email=student13@mergington.edu")
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # Use an existing participant
        response = client.delete(
            "/activities/Soccer Team/unregister?email=liam@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from the activity"""
        email = "noah@mergington.edu"
        response = client.delete(f"/activities/Soccer Team/unregister?email={email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Soccer Team"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        """Test unregister when not signed up returns 400"""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_empty_email(self, client):
        """Test unregister with empty email returns 400"""
        response = client.delete("/activities/Soccer Team/unregister?email=")
        assert response.status_code == 400
        assert response.json()["detail"] == "Email parameter is required"

    def test_unregister_invalid_email_format(self, client):
        """Test unregister with invalid email format returns 400"""
        response = client.delete("/activities/Soccer Team/unregister?email=invalidemail")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email format"


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
