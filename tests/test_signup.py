import threading
from src.app import activities
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException


def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_prevents_concurrent_duplicate_signups():
    # Arrange
    from src.app import signup_for_activity

    activity_name = "Soccer Team"
    email = "concurrent.student@mergington.edu"

    class CoordinatedParticipants(list):
        def __init__(self):
            super().__init__()
            self.contains_calls = 0
            self.second_check_started = threading.Event()
            self.count_lock = threading.Lock()

        def __contains__(self, item):
            with self.count_lock:
                self.contains_calls += 1
                is_second_call = self.contains_calls == 2
                if is_second_call:
                    self.second_check_started.set()

            if not is_second_call:
                self.second_check_started.wait(timeout=0.2)

            return super().__contains__(item)

    participants = CoordinatedParticipants()
    activities[activity_name]["participants"] = participants

    def attempt_signup():
        try:
            return signup_for_activity(activity_name, email)
        except HTTPException as exc:
            return exc.status_code, exc.detail

    # Act
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt_signup(), range(2)))

    # Assert
    assert results.count({"message": f"Signed up {email} for {activity_name}"}) == 1
    assert results.count((400, "Student is already signed up for this activity")) == 1
    assert participants == [email]
