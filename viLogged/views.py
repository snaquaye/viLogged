import json
import datetime
from django.contrib import messages
import simplejson
from django.contrib.auth.views import login_required, login as django_login, logout as django_logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, ListView, FormView
from braces.views import LoginRequiredMixin
from core.models import Visitors, VisitorsLocation, Vehicle, Appointments
from core.forms.core_forms import *
from core.models import UserProfile



def json_response(func):
    """
    A decorator that takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """

    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        if isinstance(objects, HttpResponse):
            return objects
        try:
            data = simplejson.dumps(objects)
            if 'callback' in request.REQUEST:
                # a jsonp response!
                data = '%s(%s);' % (request.REQUEST['callback'], data)
                return HttpResponse(data, "text/javascript")
        except:
            data = simplejson.dumps(str(objects))
        return HttpResponse(data, "application/json")

    return decorator


class JSONResponseMixin(object):
    def render_json(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content, content_type='application/json', **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)

@login_required
def home(request, *args, **kwargs):
    approved = Appointments.objects.all().filter(approved=True).select_related()
    in_progress = Appointments.objects.all().select_related()
    black_listed = Visitors.objects.all().filter(group_id__black_listed=True).select_related()

    context = {
        'approved': approved,
        'in_progress': in_progress,
        'black_listed': black_listed
    }
    return render(request, 'index.html', context)


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'


class VisitorsListView(LoginRequiredMixin, ListView):
    template_name = 'visitors/index.html'
    model = Visitors

    def get_queryset(self):
        query = self.model.objects.all().select_related()
        return query


class StaffsListView(LoginRequiredMixin, ListView):
    template_name = 'staff/index.html'
    model = UserProfile

    def get_queryset(self):
        query = self.model.objects.all().select_related()
        return query


class StaffFormView(LoginRequiredMixin, FormView):
    template_name = 'staff/form.html'

    def get(self, request, *args, **kwargs):
        context = super(StaffFormView, self).get_context_data(**kwargs)
        context['form'] = UserCreateForm()
        context['profile_form'] = UserProfileFrom()
        context['departments'] = CompanyDepartments.objects.all()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = super(StaffFormView, self).get_context_data(**kwargs)
        context['departments'] = CompanyDepartments.objects.all()
        profile_form = UserProfileFrom(request.POST)
        form = UserCreateForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            new_user = form.save()
            new_user.email = request.POST.get('username')
            new_user.save()
            try:
                department_id = CompanyDepartments.objects.get(uuid=request.POST.get('department'))
            except CompanyDepartments.DoesNotExist:
                department_id = None

            user_profile = UserProfile(
                user_id=new_user,
                phone=request.POST.get('phone'),
                home_phone=request.POST.get('home_phone'),
                work_phone=request.POST.get('office_phone'),
                department=department_id,
                designation=request.POST.get('designation')
            )
            user_profile.save()

            return HttpResponseRedirect("/staff-list/")
        else:
            context['form'] = form
            context['profile_form'] = profile_form
            return render(request, self.template_name, context)


class VisitorsFromView(LoginRequiredMixin, FormView):
    template_name = 'visitors/form.html'

    def get(self, request, *args, **kwargs):

        context = super(VisitorsFromView, self).get_context_data(**kwargs)
        context['visitors_form'] = VisitorsForm
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = super(VisitorsFromView, self).get_context_data(**kwargs)

        return HttpResponseRedirect('/manage/vaccine-cooler-setup')


class Reports(LoginRequiredMixin, ListView):
    template_name = 'reports/index.html'
    model = Visitors

    def get_queryset(self):
        query = self.model.objects.all().select_related()
        return query


@login_required
def add_visitor(request):
    return render(request, 'visitors/form.html', {})


def login(req, template_name=''):
    return django_login(req, **{"template_name": 'login.html'})


def logout(req, template_name=''):
    django_logout(req, **{"template_name": 'login.html'})
    return redirect('/')
