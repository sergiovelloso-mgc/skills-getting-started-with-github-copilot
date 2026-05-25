"""
Tests for the High School Management System API using AAA (Arrange-Act-Assert) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient instance for making requests to the app.
    """
    return TestClient(app)


@pytest.fixture
def fresh_activities(monkeypatch):
    """
    Fixture that provides a fresh copy of the activities database for each test.
    This ensures test isolation - changes in one test don't affect others.
    """
    original_activities = copy.deepcopy(activities)
    monkeypatch.setattr("src.app.activities", original_activities)
    return original_activities


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        ARRANGE: Set up the test client and use fresh activities database
        ACT: Make a GET request to /activities
        ASSERT: Verify response contains all activities with correct structure
        """
        # ACT
        response = client.get("/activities")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Math Club" in data

    def test_get_activities_returns_correct_structure(self, client, fresh_activities):
        """
        ARRANGE: Test client and fresh database
        ACT: Get activities
        ASSERT: Verify each activity has required fields
        """
        # ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_shows_participant_count(self, client, fresh_activities):
        """
        ARRANGE: Test client and fresh database
        ACT: Get activities
        ASSERT: Verify participant counts are correct
        """
        # ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignup:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, fresh_activities):
        """
        ARRANGE: Set up test client with fresh database and a new email
        ACT: Sign up a new student for an activity
        ASSERT: Verify signup was successful and student is in participants list
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_list(self, client, fresh_activities):
        """
        ARRANGE: Fresh database and new email
        ACT: Sign up a student
        ASSERT: Verify participant list is updated
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "alice@mergington.edu"

        # ACT
        client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )
        response = client.get("/activities")

        # ASSERT
        activities_data = response.json()
        assert email in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == 3

    def test_signup_duplicate_student_rejected(self, client, fresh_activities):
        """
        ARRANGE: Fresh database with a student already signed up
        ACT: Try to sign up the same student again
        ASSERT: Verify signup is rejected with 400 error
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        ARRANGE: Fresh database and non-existent activity name
        ACT: Try to sign up for an activity that doesn't exist
        ASSERT: Verify 404 error is returned
        """
        # ARRANGE
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_students_different_activities(self, client, fresh_activities):
        """
        ARRANGE: Fresh database
        ACT: Sign up different students for different activities
        ASSERT: Verify each signup is independent and successful
        """
        # ARRANGE
        signups = [
            ("Chess Club", "student1@mergington.edu"),
            ("Programming Class", "student2@mergington.edu"),
            ("Gym Class", "student3@mergington.edu")
        ]

        # ACT
        for activity_name, email in signups:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}",
                follow_redirects=True
            )
            assert response.status_code == 200

        # ASSERT
        response = client.get("/activities")
        activities_data = response.json()
        assert "student1@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert "student2@mergington.edu" in activities_data["Programming Class"]["participants"]
        assert "student3@mergington.edu" in activities_data["Gym Class"]["participants"]


class TestUnregister:
    """Test suite for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client, fresh_activities):
        """
        ARRANGE: Fresh database with an existing participant
        ACT: Unregister the participant from the activity
        ASSERT: Verify unregister was successful and participant is removed
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Existing participant

        # ACT
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, fresh_activities):
        """
        ARRANGE: Fresh database with participant
        ACT: Unregister the participant
        ASSERT: Verify participant list is updated correctly
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "emma@mergington.edu"

        # ACT
        client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )
        response = client.get("/activities")

        # ASSERT
        activities_data = response.json()
        assert email not in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == 1

    def test_unregister_nonexistent_participant_returns_400(self, client, fresh_activities):
        """
        ARRANGE: Fresh database and non-participating email
        ACT: Try to unregister someone not signed up
        ASSERT: Verify 400 error is returned
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"  # Not signed up

        # ACT
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        ARRANGE: Fresh database and non-existent activity
        ACT: Try to unregister from non-existent activity
        ASSERT: Verify 404 error is returned
        """
        # ARRANGE
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_then_signup_again(self, client, fresh_activities):
        """
        ARRANGE: Fresh database with participant
        ACT: Unregister and then sign up again
        ASSERT: Verify student can re-register after unregistering
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # ACT - Unregister
        response1 = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )
        assert response1.status_code == 200

        # ACT - Sign up again
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # ASSERT
        assert response2.status_code == 200
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data[activity_name]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_unregister_signup_workflow(self, client, fresh_activities):
        """
        ARRANGE: Fresh database
        ACT: Sign up, unregister, sign up again
        ASSERT: Verify complete workflow works correctly
        """
        # ARRANGE
        activity_name = "Math Club"
        email = "testuser@mergington.edu"

        # ACT - Initial signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )
        assert response1.status_code == 200

        # Get activities and verify signup
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]

        # ACT - Unregister
        response2 = client.post(
            f"/activities/{activity_name}/unregister?email={email}",
            follow_redirects=True
        )
        assert response2.status_code == 200

        # Get activities and verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]

        # ACT - Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )
        assert response3.status_code == 200

        # ASSERT - Final state
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]

    def test_multiple_concurrent_signups_same_activity(self, client, fresh_activities):
        """
        ARRANGE: Fresh database
        ACT: Sign up multiple students for the same activity
        ASSERT: Verify all signups succeed and participants are added
        """
        # ARRANGE
        activity_name = "Gym Class"
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]

        # ACT
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}",
                follow_redirects=True
            )
            assert response.status_code == 200

        # ASSERT
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants
