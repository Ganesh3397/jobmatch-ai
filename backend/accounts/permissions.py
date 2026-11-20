from rest_framework.permissions import BasePermission


class IsSeeker(BasePermission):
    message = "Only job seekers can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_seeker)


class IsRecruiter(BasePermission):
    message = "Only recruiters can do this."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_recruiter or u.is_admin_role))


class IsAdminRole(BasePermission):
    message = "Only admins can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_role)
