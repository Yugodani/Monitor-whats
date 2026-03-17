from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Screenshot
import logging

logger = logging.getLogger(__name__)


@login_required
def screenshot_list(request):
    user = request.user
    print(f"🔍 Usuário: {user.email}")

    screenshots = Screenshot.objects.filter(
        device__user=user
    ).select_related('device').order_by('-timestamp')

    print(f"📸 Total de screenshots: {screenshots.count()}")

    for s in screenshots[:5]:
        print(f"  - {s.id}: {s.image.url} - {s.timestamp}")

    paginator = Paginator(screenshots, 24)
    page = request.GET.get('page')
    screenshots_page = paginator.get_page(page)

    context = {
        'screenshots': screenshots_page,
        'total': screenshots.count(),
    }

    return render(request, 'screenshots/list.html', context)