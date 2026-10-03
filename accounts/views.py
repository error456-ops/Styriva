from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, SignupForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Profile
from selfmirror.models import (
    StyleConsultation,
    GeneratedLook,
    EvolvedLook,
)

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Your account has been created successfully.",
            )

            return redirect("generate_style_look")

    else:
        form = SignupForm()

    return render(
        request,
        "signup.html",
        {
            "form": form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                "Welcome back!",
            )

            return redirect("generate_style_look")

    else:
        form = LoginForm()

    return render(
        request,
        "login.html",
        {
            "form": form,
        },
    )


@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("login")


@login_required
def profile(request):

    consultation_count = StyleConsultation.objects.filter(
        user=request.user
    ).count()

    generated_look_count = GeneratedLook.objects.filter(
        consultation__user=request.user
    ).count()

    evolved_look_count = EvolvedLook.objects.filter(
        generated_look__consultation__user=request.user
    ).count()

    recent_looks = GeneratedLook.objects.filter(
        consultation__user=request.user
    ).order_by("-created_at")[:6]

    context = {
        "profile": request.user.profile,
        "consultation_count": consultation_count,
        "generated_look_count": generated_look_count,
        "evolved_look_count": evolved_look_count,
        "recent_looks": recent_looks,
    }

    return render(
        request,
        "profile.html",
        context,
    )