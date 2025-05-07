import pytest
from api.common import Permissions
from api.models import User, Province
from tests.factories.factories import ProvinceFactory


@pytest.mark.django_db
def test_province_for_user(seed_loader):
    seed_loader.load_permissions()
    seed_loader.seed_users()

    provinces = ProvinceFactory.create_batch(3)
    province = provinces[1]
    province_user = User.find_by(username='province')
    province_user.provinces.add(province)
    province_user.save()

    assert province_user
    assert Permissions.has_permission(province_user, Permissions.Codes.SCHEDULE_VA) is True
    assert Permissions.has_permission(province_user, Permissions.Codes.VIEW_ASSIGNED_PROVINCES) is True
    assert Permissions.has_permission(province_user, Permissions.Codes.VIEW_ALL_PROVINCES) is False

    user_provinces = list(Province.objects.for_user(province_user))
    assert user_provinces == [province]
