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
    print(f"🔍 User ID: {user.id}")

    screenshots = Screenshot.objects.filter(
        device__user=user
    ).select_related('device').order_by('-timestamp')

    print(f"📸 Total de screenshots no banco: {screenshots.count()}")

    for s in screenshots[:5]:
        print(f"  - ID: {s.id}")
        print(f"    Device: {s.device.device_name}")
        print(f"    Timestamp: {s.timestamp}")
        print(f"    Image URL: {s.image.url}")
        print(f"    Image path: {s.image.path}")

    paginator = Paginator(screenshots, 24)
    page = request.GET.get('page')
    screenshots_page = paginator.get_page(page)

    context = {
        'screenshots': screenshots_page,
        'total': screenshots.count(),
    }

    return render(request, 'screenshots/list.html', context)