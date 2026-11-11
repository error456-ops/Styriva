
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import LoginForm, SignupForm
from .models import Profile

from selfmirror.models import (
    StyleConsultation,
    GeneratedLook,
    EvolvedLook,
    PieceStyling,
    PieceStylingResult,
)


def transfer_guest_piece_stylings(request, user):
    """
    Transfer guest styling sessions recorded
    in this browser session to the newly authenticated user.
    """

    guest_ids = request.session.get("style_my_piece_ids", [])

    valid_ids = []

    for piece_id in guest_ids:
        try:
            valid_ids.append(int(piece_id))
        except (TypeError, ValueError):
            continue

    if not valid_ids:
        return None

    guest_pieces = PieceStyling.objects.filter(
        pk__in=valid_ids,
        user__isnull=True,
    )

    transferable_ids = list(
        guest_pieces.values_list("pk", flat=True)
    )

    if not transferable_ids:
        return None

    guest_pieces.update(user=user)

    latest_piece_id = next(
        (
            piece_id
            for piece_id in reversed(valid_ids)
            if piece_id in transferable_ids
        ),
        None,
    )

    request.session.pop("style_my_piece_ids", None)

    if latest_piece_id:
        request.session["style_my_piece_resume_id"] = latest_piece_id

    return latest_piece_id


def signup_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            piece_id = transfer_guest_piece_stylings(
                request,
                user,
            )

            messages.success(
                request,
                "Your account has been created successfully.",
            )

            if piece_id:
                return redirect(
                    f"{reverse('style_my_piece')}?piece_id={piece_id}"
                )

            return redirect("generate_style_look")

    else:
        form = SignupForm()

    return render(
        request,
        "signup.html",
        {"form": form},
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            login(request, user)

            piece_id = transfer_guest_piece_stylings(
                request,
                user,
            )

            messages.success(
                request,
                "Welcome back!",
            )

            if piece_id:
                return redirect(
                    f"{reverse('style_my_piece')}?piece_id={piece_id}"
                )

            return redirect("generate_style_look")

    else:
        form = LoginForm()

    return render(
        request,
        "login.html",
        {"form": form},
    )


@login_required
def profile(request):

    # ==========================================
    # WARDROBE HISTORY
    # ==========================================

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

    # ==========================================
    # STYLE MY PIECE HISTORY
    # ==========================================

    piece_look_count = PieceStylingResult.objects.filter(
        piece_styling__user=request.user
    ).count()

    recent_piece_looks = (
        PieceStylingResult.objects
        .filter(piece_styling__user=request.user)
        .select_related("piece_styling")
        .order_by("-created_at")[:12]
    )

    # ==========================================
    # PROFILE CONTEXT
    # ==========================================

    context = {
        "profile": request.user.profile,

        # Wardrobe
        "consultation_count": consultation_count,
        "generated_look_count": generated_look_count,
        "evolved_look_count": evolved_look_count,
        "recent_looks": recent_looks,

        # Style My Piece
        "piece_look_count": piece_look_count,
        "recent_piece_looks": recent_piece_looks,
    }

    return render(
        request,
        "profile.html",
        context,
    )


def logout_view(request):
    logout(request)
    return redirect("login")
