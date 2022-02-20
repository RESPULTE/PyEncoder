import pytest

@pytest.fixture
def StringData():
    return (
        "Never gonna give you up Never gonna let you down Never gonna run around and desert you Never gonna make you cry Never gonna say goodbye Never gonna tell a lie and hurt you"
    )


@pytest.fixture()
def ListintegerData():
    return [69, 69, 69, 69, 420, 420, 420, 420, 111, 111, 911, 911, 888]