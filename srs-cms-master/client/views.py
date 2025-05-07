from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Value
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from api.models import Death, Province
from api.common import Permissions, TypeCaster
from client.forms import DeathForm


@login_required(login_url="/login/")
def home(request):
    return render(request, 'client/home.html')


@login_required(login_url="/login/")
def deaths_home(request):
    province_id = request.GET.get('province')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    query = request.GET.get('q', '').strip()
    paging_size = TypeCaster.to_int(request.GET.get('paging_size', 10), default=10)

    provinces = Province.objects.for_user(request.user)
    can_schedule_va = Permissions.has_permission(request, Permissions.Codes.SCHEDULE_VA)
    can_view_all_provinces = Permissions.has_permission(request, Permissions.Codes.VIEW_ALL_PROVINCES)

    selected_province = None
    if province_id:
        selected_province = provinces.get(id=province_id)
    elif not can_view_all_provinces:
        selected_province = provinces.first()

    filters = {}
    if selected_province:
        filters['event__cluster__province_id'] = selected_province
    if start_date and end_date:
        filters['deceased_dod__gte'] = parse_date(start_date)
        filters['deceased_dod__lte'] = parse_date(end_date)
    else:
        if start_date:
            filters['deceased_dod'] = parse_date(start_date)
        elif end_date:
            filters['deceased_dod'] = parse_date(end_date)

    new_deaths = Death.objects.filter(death_status=Death.DeathStatus.NEW_DEATH, **filters)
    scheduled_deaths = Death.objects.filter(death_status=Death.DeathStatus.VA_SCHEDULED, **filters)
    completed_deaths = Death.objects.filter(death_status=Death.DeathStatus.VA_COMPLETED, **filters)

    # Text search
    if query:
        # Search weights for each field.
        similarity = (
                0.5 * TrigramSimilarity(Coalesce(F('death_code'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('va_staff__code'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('event__event_staff__code'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('event__area__code'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('event__household_head_name'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('deceased_name'), Value('')), query) +
                0.4 * TrigramSimilarity(Coalesce(F('event__respondent_name'), Value('')), query)
        )
        min_similarity = 0.05

        new_deaths = new_deaths.annotate(similarity=similarity).filter(
            similarity__gte=min_similarity).order_by('-similarity')

        scheduled_deaths = scheduled_deaths.annotate(similarity=similarity).filter(
            similarity__gte=min_similarity).order_by('-similarity')

        completed_deaths = completed_deaths.annotate(similarity=similarity).filter(
            similarity__gte=min_similarity).order_by('-similarity')

    # Paginate
    new_deaths, new_deaths_paginator, scheduled_deaths, scheduled_deaths_paginator, completed_deaths, completed_deaths_paginator = (
        paginate(request,
                 page_keys=['new_deaths_page', 'scheduled_deaths_page', 'completed_deaths_page'],
                 items=[new_deaths, scheduled_deaths, completed_deaths],
                 page_size=paging_size
                 )
    )

    return render(
        request,
        'client/death_management/home.html',
        {
            'can_schedule_va': can_schedule_va,
            'can_view_all_provinces': can_view_all_provinces,
            'provinces': provinces,
            'selected_province': selected_province,
            'start_date': start_date,
            'end_date': end_date,
            'query': query,
            'paging_size': paging_size,
            'paging_sizes': [10, 20, 50, 100],

            'new_deaths': new_deaths,
            'new_deaths_paginator': new_deaths_paginator,
            'new_deaths_total': new_deaths_paginator.count,
            'new_deaths_page_total': len(new_deaths.object_list),

            'scheduled_deaths': scheduled_deaths,
            'scheduled_deaths_paginator': scheduled_deaths_paginator,
            'scheduled_deaths_total': scheduled_deaths_paginator.count,
            'scheduled_deaths_page_total': len(scheduled_deaths.object_list),

            'completed_deaths': completed_deaths,
            'completed_deaths_paginator': completed_deaths_paginator,
            'completed_deaths_total': completed_deaths_paginator.count,
            'completed_deaths_page_total': len(completed_deaths.object_list),
        }
    )


@login_required(login_url="/login/")
def deaths_edit(request, id):
    death = get_object_or_404(Death, id=id)
    is_readonly = death.death_status == Death.DeathStatus.VA_COMPLETED

    if request.method == 'POST':
        form = DeathForm(request.POST, instance=death, is_readonly=is_readonly)
        if form.is_valid():
            form.save()
            return redirect('deaths_home')
    else:
        form = DeathForm(instance=death, is_readonly=is_readonly)
    return render(request, 'client/death_management/edit.html', {'form': form})


def paginate(request, page_keys=[], items=[], page_size=10):
    results = []
    for index, page_key in enumerate(page_keys):
        page_number = request.GET.get(page_key, 1)
        page_items = items[index] or []
        paginator = Paginator(page_items, page_size)
        try:
            page_items = paginator.page(page_number)
        except PageNotAnInteger:
            page_items = paginator.page(1)
        except EmptyPage:
            page_items = paginator.page(paginator.num_pages)
        results.append(page_items)
        results.append(paginator)

    return results
