import pytest
from api.common import Permissions
from api.models import User


@pytest.mark.django_db
def test_permissions_work(seed_loader):
    seed_loader.load_permissions()
    seed_loader.seed_users()
    user = User.find_by(username='province')
    assert user
    assert Permissions.has_permission(user, Permissions.Codes.SCHEDULE_VA) is True
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ASSIGNED_PROVINCES) is True
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ALL_PROVINCES) is False

    user = User.find_by(username='central')
    assert user
    assert Permissions.has_permission(user, Permissions.Codes.SCHEDULE_VA) is True
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ASSIGNED_PROVINCES) is False
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ALL_PROVINCES) is True

    user = User.find_by(username='administrator')
    assert user
    assert Permissions.has_permission(user, Permissions.Codes.SCHEDULE_VA) is True
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ASSIGNED_PROVINCES) is False
    assert Permissions.has_permission(user, Permissions.Codes.VIEW_ALL_PROVINCES) is True
