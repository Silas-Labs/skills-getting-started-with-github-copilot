"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestApiEndpoints:
    """Test basic API endpoints"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify structure
        assert isinstance(activities, dict)
        assert "Basketball" in activities
        assert "Tennis Club" in activities
        assert "Drama Club" in activities
        
        # Verify activity structure
        basketball = activities["Basketball"]
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)

    def test_activity_has_sample_participants(self):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check Basketball has at least one participant
        assert len(activities["Basketball"]["participants"]) >= 1
        assert "alex@mergington.edu" in activities["Basketball"]["participants"]


class TestSignup:
    """Test signup functionality"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Basketball" in result["message"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_duplicate_email(self):
        """Test that duplicate signups are rejected"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]


class TestUnregister:
    """Test unregister functionality"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        # First, sign up a student
        client.post(
            "/activities/Tennis%20Club/signup?email=unregtest@mergington.edu"
        )
        
        # Then unregister them
        response = client.delete(
            "/activities/Tennis%20Club/unregister?email=unregtest@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]

    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistentActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_not_signed_up(self):
        """Test unregister for student not signed up"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removetest@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Art%20Studio/signup?email={email}")
        
        # Verify participant is in list
        response1 = client.get("/activities")
        participants1 = response1.json()["Art Studio"]["participants"]
        assert email in participants1
        
        # Unregister
        client.delete(f"/activities/Art%20Studio/unregister?email={email}")
        
        # Verify participant is removed
        response2 = client.get("/activities")
        participants2 = response2.json()["Art Studio"]["participants"]
        assert email not in participants2


class TestActivitySpots:
    """Test activity spot availability"""

    def test_activities_have_spot_capacity(self):
        """Test that activities have max_participants defined"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "max_participants" in activity_data
            assert activity_data["max_participants"] > 0
            assert "participants" in activity_data
            # Participants should not exceed max
            assert len(activity_data["participants"]) <= activity_data["max_participants"]
