from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Screenshot


@login_required
def screenshot_list(request):
    user = request.user
    screenshots = Screenshot.objects.filter(
        device__user=user
    ).select_related('device').order_by('-timestamp')

    paginator = Paginator(screenshots, 24)
    page = request.GET.get('page')
    screenshots_page = paginator.get_page(page)

    context = {
        'screenshots': screenshots_page,
        'total': screenshots.count(),
        'last_7_days': screenshots.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }

    return render(request, 'screenshots/list.html', context)