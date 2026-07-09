from django.shortcuts import redirect
from django.urls import reverse
from legal.models import TermsVersion, UserConsent

class LegalConsentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Paths that are exempted from the mandatory terms check
        path = request.path_info
        if (path.startswith('/legal/') or 
            path.startswith('/admin/') or 
            path.startswith('/logout') or 
            path.startswith('/users/logout') or
            path.startswith('/static/') or 
            path.startswith('/media/')):
            return self.get_response(request)

        # Check if there are active terms
        active_terms = TermsVersion.objects.filter(is_active=True).values_list('id', flat=True)
        if not active_terms:
            return self.get_response(request)

        # Check if the user has a valid, active consent for any of the active terms versions
        has_consent = UserConsent.objects.filter(
            user=request.user,
            terms_version_id__in=active_terms,
            is_active=True
        ).exists()

        if not has_consent:
            # Enforce the block
            return redirect(reverse('legal:accept_terms'))

        return self.get_response(request)
