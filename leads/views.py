from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import LeadForm, StatusForm
from .models import Lead


@login_required
def lead_list(request):
    leads = Lead.objects.all()
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "")
    if search:
        leads = leads.filter(Q(name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search) | Q(source__icontains=search))
    error = ""
    if status:
        if status not in Lead.Status.values:
            error = "Noto‘g‘ri status tanlandi."
            leads = leads.none()
        else:
            leads = leads.filter(status=status)
    counts = dict(Lead.objects.values_list("status").annotate(total=Count("pk")))
    return render(request, "leads/list.html", {
        "page_obj": Paginator(leads, 10).get_page(request.GET.get("page")),
        "search": search, "status": status, "statuses": Lead.Status.choices,
        "error": error, "total": sum(counts.values()),
        "new_count": counts.get("New", 0), "won_count": counts.get("Won", 0),
    })


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    return render(request, "leads/detail.html", {"lead": lead, "status_form": StatusForm(instance=lead)})


@login_required
def lead_form(request, pk=None):
    lead = get_object_or_404(Lead, pk=pk) if pk is not None else None
    form = LeadForm(request.POST if request.method == "POST" else None, instance=lead)
    if request.method == "POST" and form.is_valid():
        lead = form.save()
        messages.success(request, "Lead saqlandi.")
        return redirect("lead-detail", pk=lead.pk)
    return render(request, "leads/form.html", {"form": form, "lead": lead})


@login_required
@require_POST
def lead_status(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    form = StatusForm(request.POST, instance=lead)
    if form.is_valid():
        form.save()
        messages.success(request, "Status yangilandi.")
        return redirect("lead-detail", pk=pk)
    return render(request, "leads/detail.html", {"lead": lead, "status_form": form}, status=400)


@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        lead.delete()
        messages.success(request, "Lead o‘chirildi.")
        return redirect("lead-list")
    return render(request, "leads/delete.html", {"lead": lead})
