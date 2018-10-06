"""SmartValve URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import Smart_Valve.views
import Smart_Valve.OrganizationViews
import Smart_Valve.OrgAdminViews
import Smart_Valve.UserViews
import Smart_Valve.ValvesViews

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', Smart_Valve.views.LoginView.as_view(), name='login'),
    url(r'^authenticate/', Smart_Valve.views.AuthenticateView.as_view(), name='authenticate'),
    url(r'^dashboard/', Smart_Valve.views.DashBoardView.as_view(), name='dashboard'),
    url(r'^organization_create/',Smart_Valve.OrganizationViews.OrganizationCreateView.as_view(), name='organization_create'),
    url(r'^organization_list/', Smart_Valve.OrganizationViews.OrganizationListView.as_view(), name='organization_list'),
    url(r'^organization/(?P<pk>\d+)/edit', Smart_Valve.OrganizationViews.OrganizationUpdateView.as_view(), name='organization_update'),
    url(r'^org_admins/create', Smart_Valve.OrgAdminViews.OrgAdminCreateView.as_view(), name='org_admin_create_view'),
    url(r'^org_admins/list/', Smart_Valve.OrgAdminViews.OrgAdminListView.as_view(), name='org_admin_list_view'),
    url(r'^users/create/', Smart_Valve.UserViews.UserCreateView.as_view(), name='user_create_view'),
    url(r'^users/list/', Smart_Valve.UserViews.UserListView.as_view(), name='user_list_view'),
    url(r'^valves/create/', Smart_Valve.ValvesViews.ValveCreateView.as_view(), name='valve_create_view'),
    url(r'^valves/list/', Smart_Valve.ValvesViews.ValveListView.as_view(), name='valve_list_view'),
    url(r'^valves/update/(?P<pk>\d+)', Smart_Valve.ValvesViews.ValveEditView.as_view(), name='valve_edit_view'),
    url(r'^logout/', Smart_Valve.views.LogoutView.as_view(), name='logout_view'),
]
