from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import ClientProfile


def get_profile(user):
    profile, _ = ClientProfile.objects.get_or_create(user=user)
    return profile


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_get(request):
    p = get_profile(request.user)

    data = {
        "full_name": p.full_name,
        "email": request.user.email,
        "phone": p.phone,
        "company": p.company,
        "address": p.address,
        "profile_image": p.profile_image.url if p.profile_image else None,
        "client_id": p.client_id,
        "member_since": p.member_since,
        "is_active": p.is_active,
    }
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile_update(request):
    p = get_profile(request.user)

    # Update normal fields (partial update)
    p.full_name = request.data.get("full_name", p.full_name)
    p.phone = request.data.get("phone", p.phone)
    p.company = request.data.get("company", p.company)
    p.address = request.data.get("address", p.address)

    # Update email (User model)
    if "email" in request.data:
        request.user.email = request.data.get("email", request.user.email)
        request.user.save()

    # Update profile image (if sent)
    if "profile_image" in request.FILES:
        p.profile_image = request.FILES["profile_image"]

    p.save()

    data = {
        "full_name": p.full_name,
        "email": request.user.email,
        "phone": p.phone,
        "company": p.company,
        "address": p.address,
        "profile_image": p.profile_image.url if p.profile_image else None,
        "client_id": p.client_id,
        "member_since": p.member_since,
        "is_active": p.is_active,
    }
    return Response({"ok": True, "data": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def profile_remove_photo(request):
    p = get_profile(request.user)

    if p.profile_image:
        p.profile_image.delete(save=False)
        p.profile_image = None
        p.save()

    return Response({"ok": True})