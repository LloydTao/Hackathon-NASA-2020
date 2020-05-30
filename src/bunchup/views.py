from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Hub, Activity

class HomeView(ListView):
    model = Hub
    template_name = 'bunchup/index.html'
    context_object_name = 'hubs'

class HubView(DetailView):
    model = Hub
    
    def get_context_data(self, **kwargs):
        context = super(HubView, self).get_context_data(**kwargs)
        hub = self.get_object()
        members = hub.membership_set.filter()
        admins = []
        for member in members:
            if member.is_admin:
                admins.append(member.user)
        context['admins'] = admins
        return context

class HubCreateView(LoginRequiredMixin, CreateView):
    model = Hub
    context_object_name = 'hubs'
    fields = ['name', 'description', 'locked', 'tags']

class HubUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Hub
    context_object_name = 'hubs'
    template_name = 'bunchup/hub_update.html'
    fields = ['name', 'description', 'locked', 'tags']
    
    def test_func(self):
        hub = self.get_object()
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class HubDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Hub
    success_url = '/'
        
    def test_func(self):
        hub = self.get_object()
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False




class ActivityView(DetailView):
    model = Activity
    template_name = 'bunchup/activity.html'
    context_object_name = 'activities'


class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    context_object_name = 'activities'
    fields = ['name', 'description', 'start_date', 'finish_date']
