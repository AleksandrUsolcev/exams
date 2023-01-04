from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView, )
from django.urls import path, reverse_lazy

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        LogoutView.as_view(
            template_name='users/logout.html',
            next_page='questions:index'
        ),
        name='logout'
    ),
    path('signup/',
         views.SignupView.as_view(),
         name='signup'),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path('password_reset/',
         PasswordResetView.as_view(
             template_name="users/password_reset_form.html",
             email_template_name='users/password_reset_email.html',
             success_url=reverse_lazy('users:password_reset_done')),
         name='password_reset_form'),
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'password_reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('users:password_reset_complete')),
        name='password_reset_confirm'
    ),
    path(
        'password_reset/complete/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_change_complete.html'),
        name='password_reset_complete'
    ),
    path(
        'password-change/',
        PasswordChangeView.as_view(
            template_name='users/password_change_form.html',
            success_url=reverse_lazy('users:password_change_done')),
        name='password_change_form'
    ),
    path(
        'password-change/done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'
    ),
    path('@<slug:username>', views.UserProfileView.as_view(), name='profile'),
    path(
        '@<slug:username>/edit/',
        views.UserEditView.as_view(),
        name='profile_edit'
    ),
    path(
        'progress/<int:pk>/',
        views.UserProgressDetailView.as_view(),
        name='progress_detail'
    ),
    path(
        'rankings/', views.RankingListView.as_view(), name='users_rankings'
    )
]
