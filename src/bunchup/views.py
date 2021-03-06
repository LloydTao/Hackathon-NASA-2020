from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View

from tagging.models import Tag, TaggedItem
from titlecase import titlecase

from .models import Hub, Activity, Membership, Room
from .forms import ImageUploadForm

class HomeView(ListView):
    model = Hub
    template_name = 'bunchup/index.html'
    context_object_name = 'hubs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["highlights"] = {}

        featured = Hub.objects.all()
        context["highlights"]["Featured Hubs"] = featured

        activities = Activity.objects.all()
        context["highlights"]["Activities"] = activities

        for tag in Tag.objects.all():
            titled_tag_name = titlecase(tag.name)

            try:
                tag_hubs = TaggedItem.objects.get_by_model(Hub, tag)

                if len(tag_hubs) > 0:
                    context["highlights"][f"{titled_tag_name} Hubs"] = tag_hubs
            except Tag.DoesNotExist:
                pass

            try:
                tag_activities = TaggedItem.objects.get_by_model(Activity, tag)

                if len(tag_activities) > 0:
                    context["highlights"][f"{titled_tag_name} Activities"] = tag_activities
            except Tag.DoesNotExist:
                pass

        return context
    

class HubView(DetailView):
    model = Hub
    
    def get_context_data(self, **kwargs):
        context = super(HubView, self).get_context_data(**kwargs)
        hub = self.get_object()
        members = hub.membership_set.filter()
        admins = []
        users = []
        context['total_users'] = len(hub.users.all())
        for member in members:
            users.append(member.user)
            if member.is_admin:
                admins.append(member.user)
        context['activities'] = Activity.objects.filter(hub=self.kwargs.get('pk'))
        context['next_activity'] = context['activities'][0] if context['activities'] else None
        context['users'] = users
        context['admins'] = admins
        return context

class HubCreateView(LoginRequiredMixin, CreateView):
    model = Hub
    form_class = ImageUploadForm

    def form_valid(self, form):
        self.object = form.save()
        Membership.objects.create(
            user=self.request.user,
            hub=self.object,
            is_admin=True
        )
        general_room = Room(name="General",
                            description="A general room to discuss anything.",
                            hub=self.object,
                            activity_room=False)
        general_room.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(self.object.pk)}))


class HubUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Hub
    form_class = ImageUploadForm
    context_object_name = 'hubs'
    template_name = 'bunchup/hub_update.html'

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(self.object.pk)}))

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
    context_object_name = 'activity'

    def get_context_data(self, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        activity = self.get_object()
        total_users = len(activity.users.all())

        context["chat_messages"] = activity.room.messages.all()

        return context


class ActivityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Activity
    context_object_name = 'activities'
    fields = ['name', 'description', 'tags', 'start_date', 'finish_date']

    def form_valid(self, form):
        self.object = form.save()
        pk = self.kwargs['pk']
        self.object.hub = Hub.objects.get(pk=pk)
        self.object.users.add(self.request.user)
        room = Room(name=self.object.name,
                    description=self.object.description,
                    hub=self.object.hub,
                    activity_room=True
                    )
        room.save()
        self.object.room = room
        self.object.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-activity", kwargs={"pk": str(self.object.pk)}))

    def test_func(self):
        hub = Hub.objects.get(pk=self.kwargs['pk'])
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class ActivityDeleteView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Activity
    success_url = "/"

    def test_func(self):
        hub = self.object.hub
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class ActivityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Activity
    context_object_name = 'activities'
    template_name = 'bunchup/activity_update.html'
    fields = ['name', 'description', 'tags', 'start_date', 'finish_date', 'image']

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-activity", kwargs={"pk": str(self.object.pk)}))

    def test_func(self):
        hub = self.get_object().hub
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class ActivityJoinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        activity = Activity.objects.get(pk=kwargs['pk'])
        activity.users.add(self.request.user)
        activity.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-activity", kwargs={"pk": str(activity.pk)}))


class HubJoinView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        hub = Hub.objects.get(pk=kwargs['pk'])
        hub.users.add(self.request.user)
        hub.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(hub.pk)}))


class HubLeaveView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        hub = Hub.objects.get(pk=kwargs['pk'])
        hub.users.remove(self.request.user)
        hub.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(hub.pk)}))


class ActivityLeaveView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        activity = Activity.objects.get(pk=kwargs['pk'])
        activity.users.remove(self.request.user)
        activity.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-activity", kwargs={"pk": str(activity.pk)}))


class RoomCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Room
    context_object_name = 'rooms'
    fields = ['name', 'description']

    def form_valid(self, form):
        self.object = form.save()
        pk = self.kwargs['pk']
        self.object.hub = Hub.objects.get(pk=pk)
        self.object.save()
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(pk)}))

    def test_func(self):
        hub = Hub.objects.get(pk=self.kwargs['pk'])
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class RoomUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Room
    context_object_name = 'rooms'
    fields = ['name', 'description']

    def form_valid(self, form):
        self.object = form.save()
        pk = self.object.hub.pk
        return HttpResponseRedirect(reverse_lazy("bunchup-hub", kwargs={"pk": str(pk)}))

    def test_func(self):
        hub = self.get_object().hub
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False


class RoomDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Room
    success_url = '/'

    def test_func(self):
        hub = self.get_object().hub
        if hub.membership_set.filter(user=self.request.user).exists():
            return hub.membership_set.get(user=self.request.user).is_admin
        else:
            return False

