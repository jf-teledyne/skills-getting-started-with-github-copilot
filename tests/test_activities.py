from src.app import activities


def test_get_activities_returns_all_activity_details(client):
    # Arrange
    expected_activity_names = set(activities)
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert set(response_activities) == expected_activity_names
    assert all(set(details) == expected_fields for details in response_activities.values())
    assert response_activities["Chess Club"]["participants"] == activities["Chess Club"]["participants"]
