import json
import logging

import razorpay

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import Payment
from accounts.services import CreditManager
from jobs.constants import JobStatus, JobType
from jobs.models import Job
from jobs.queue import JobQueue
from media_manager.manager import MediaManager

from .abuse_protection import is_rate_limited
from .models import (
    EvolvedLook,
    GeneratedLook,
    PieceStyling,
    StyleConsultation,
)

logger = logging.getLogger(__name__)


# ==========================================================
# Constants
# ==========================================================

RAZORPAY_PLANS = {
    "starter": {"name": "Starter", "amount": 19900, "credits": 20},
    "premium": {"name": "Premium", "amount": 39900, "credits": 50},
    "creator": {"name": "Creator", "amount": 69900, "credits": 100},
}

# Style My Piece: the first batch of looks is free (guests included).
# Every further batch of FREE_PIECE_LOOKS looks costs one credit
# and requires an account.
FREE_PIECE_LOOKS = 6


# ==========================================================
# Helpers
# ==========================================================

def rate_limited_response():
    return JsonResponse(
        {
            "success": False,
            "rate_limited": True,
            "message": "Too many requests. Please wait a moment and try again.",
        },
        status=429,
    )


def razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


# ==========================================================
# Splash / Feature chooser
# ==========================================================

def splash(request):
    return render(request, "splash.html")


def choose_feature(request):
    return render(request, "choose_feature.html")


# ==========================================================
# Generate Style Look
# ==========================================================

def generate_style_look(request):

    if request.method != "POST":
        return render(request, "generate_style_look.html")

    # ------------------------------------------------------
    # Abuse protection
    # ------------------------------------------------------
    if is_rate_limited(request):
        return rate_limited_response()

    # ------------------------------------------------------
    # Complimentary guest session check
    # ------------------------------------------------------
    if not request.user.is_authenticated:

        if request.session.get("free_generation_used", False):
            return JsonResponse(
                {
                    "success": False,
                    "requires_signup": True,
                    "redirect_url": reverse("signup"),
                    "message": (
                        "Your complimentary styling session "
                        "has been completed."
                    ),
                },
                status=403,
            )

    # ------------------------------------------------------
    # Authenticated user credit check
    # ------------------------------------------------------
    else:

        if not CreditManager.can_generate(request.user):
            return JsonResponse(
                {
                    "success": False,
                    "requires_upgrade": True,
                    "message": (
                        "You've used your free styling session "
                        "and have no credits remaining."
                    ),
                },
                status=403,
            )

    # ------------------------------------------------------
    # STEP 1: Collect uploaded images
    #
    # Only the user's own photo is required. Tops, bottoms,
    # one-pieces, shoes and scarves are optional, but at least
    # ONE garment (top, bottom or one-piece) is needed.
    # ------------------------------------------------------
    user_model_photo = request.FILES.get("user_model_photo")

    optional_files = {}

    for prefix in ("top", "bottom", "dress", "shoe", "scarf"):
        for i in range(1, 4):
            field = f"{prefix}_{i}"
            optional_files[field] = request.FILES.get(field)

    uploaded_files = {
        "user_model_photo": user_model_photo,
        **optional_files,
    }

    # ------------------------------------------------------
    # STEP 2: Required photo + at least one garment
    # ------------------------------------------------------
    if user_model_photo is None:
        return JsonResponse(
            {"success": False, "message": "Please upload your photo."},
            status=400,
        )

    garment_fields = [
        f"{prefix}_{i}"
        for prefix in ("top", "bottom", "dress")
        for i in range(1, 4)
    ]

    if not any(optional_files[field] is not None for field in garment_fields):
        return JsonResponse(
            {
                "success": False,
                "message": "Please upload at least one top, bottom or one-piece.",
            },
            status=400,
        )

    # ------------------------------------------------------
    # STEP 3: Validate uploaded images
    # ------------------------------------------------------
    media_manager = MediaManager()

    for field_name, uploaded_file in uploaded_files.items():

        if uploaded_file is None:
            continue

        label = field_name.replace("_", " ")

        try:
            is_valid, message = media_manager.validate_upload(uploaded_file)

        except Exception:
            logger.exception("Upload validation failed for %s", field_name)
            return JsonResponse(
                {
                    "success": False,
                    "message": f"We could not validate {label}.",
                },
                status=400,
            )

        if not is_valid:
            return JsonResponse(
                {"success": False, "message": f"Invalid {label}: {message}"},
                status=400,
            )

    # ------------------------------------------------------
    # STEP 4: Create style consultation
    # ------------------------------------------------------
    try:
        consultation = StyleConsultation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            gender=request.POST.get("gender"),
            occasion=request.POST.get("occasion"),
            vibe=request.POST.get("vibe"),
            weather=request.POST.get("weather"),
            user_model_photo=user_model_photo,
            # Any garment that was not uploaded is saved as empty.
            **optional_files,
        )

    except Exception:
        logger.exception("Style consultation creation failed")
        return JsonResponse(
            {
                "success": False,
                "message": "We could not create your style consultation.",
            },
            status=500,
        )

    # ------------------------------------------------------
    # STEP 5: Create background generation job + spend credit
    # ------------------------------------------------------
    try:
        JobQueue.create_style_generation_job(consultation)

        if request.user.is_authenticated:
            CreditManager.consume_generation(request.user)

    except Exception:
        logger.exception("Style generation job creation failed")
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Your images were uploaded, but we could not "
                    "start style generation."
                ),
            },
            status=500,
        )

    # ------------------------------------------------------
    # STEP 6: Redirect to loading / result page
    # ------------------------------------------------------
    return JsonResponse(
        {
            "success": True,
            "redirect_url": reverse(
                "result_view",
                kwargs={"consultation_id": consultation.id},
            ),
        }
    )


# ==========================================================
# Result View
# ==========================================================

def result_view(request, consultation_id):

    consultation = get_object_or_404(StyleConsultation, id=consultation_id)

    generated_look = (
        GeneratedLook.objects
        .filter(consultation=consultation)
        .order_by("-created_at")
        .first()
    )

    if generated_look is None:
        return render(request, "loading.html", {"consultation": consultation})

    # Guest has successfully completed their complimentary session.
    if not request.user.is_authenticated:
        request.session["free_generation_used"] = True
        request.session.modified = True

    return render(
        request,
        "result.html",
        {
            "consultation": consultation,
            "generated_look": generated_look,
        },
    )


# ==========================================================
# Generate Style Evolution
# ==========================================================

def generate_style_evolution(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "POST request required."},
            status=405,
        )

    if is_rate_limited(request):
        return rate_limited_response()

    # ------------------------------------------------------
    # Complimentary guest session / credit check
    # ------------------------------------------------------
    if not request.user.is_authenticated:

        if request.session.get("free_evolution_used", False):
            return JsonResponse(
                {
                    "success": False,
                    "requires_signup": True,
                    "redirect_url": reverse("signup"),
                    "message": (
                        "Your complimentary Style Evolution "
                        "has been completed."
                    ),
                },
                status=403,
            )

    else:

        if not CreditManager.can_evolve(request.user):
            return JsonResponse(
                {
                    "success": False,
                    "requires_upgrade": True,
                    "message": (
                        "You need at least one credit "
                        "to use Style Evolution."
                    ),
                },
                status=403,
            )

    consultation = None

    try:
        consultation = get_object_or_404(
            StyleConsultation,
            id=request.POST.get("consultation_id"),
        )

        style_preference = request.POST.get("style_preference", "minimal")
        extras = request.POST.getlist("extras[]")

        consultation.style_evolution_status = "processing"
        consultation.save(update_fields=["style_evolution_status"])

        JobQueue.create_style_evolution_job(
            consultation=consultation,
            style_preference=style_preference,
            extras=extras,
        )

        # Mark complimentary session used / spend credit.
        if not request.user.is_authenticated:
            request.session["free_evolution_used"] = True
            request.session.modified = True
        else:
            CreditManager.consume_style_evolution(request.user)

        return JsonResponse({"success": True, "status": "processing"})

    except Exception as error:

        logger.exception("Style evolution failed to start")

        if consultation is not None:
            consultation.style_evolution_status = "failed"
            consultation.save(update_fields=["style_evolution_status"])

        return JsonResponse(
            {"success": False, "status": "failed", "message": str(error)},
            status=500,
        )


# ==========================================================
# Generation Status
# ==========================================================

def generation_status(request, consultation_id):

    consultation = get_object_or_404(StyleConsultation, id=consultation_id)

    generated_look = (
        GeneratedLook.objects
        .filter(consultation=consultation)
        .order_by("-created_at")
        .first()
    )

    if generated_look is not None:
        return JsonResponse({"completed": True, "status": "completed"})

    job = (
        Job.objects
        .filter(
            consultation=consultation,
            job_type=JobType.STYLE_GENERATION,
        )
        .order_by("-created_at")
        .first()
    )

    if job is None:
        return JsonResponse({"completed": False, "status": "pending"})

    if job.job_status == JobStatus.FAILED:
        return JsonResponse(
            {
                "completed": False,
                "status": "failed",
                "message": job.error_message or "Style generation failed.",
            }
        )

    if job.job_status == JobStatus.COMPLETED:
        return JsonResponse(
            {
                "completed": False,
                "status": "failed",
                "message": (
                    "Style generation finished, "
                    "but no generated look was found."
                ),
            }
        )

    if job.job_status == JobStatus.RUNNING:
        return JsonResponse({"completed": False, "status": "processing"})

    return JsonResponse({"completed": False, "status": "pending"})


# ==========================================================
# Style Evolution Status
# ==========================================================

def style_evolution_status(request, consultation_id):

    consultation = get_object_or_404(StyleConsultation, id=consultation_id)

    evolved = (
        EvolvedLook.objects
        .filter(generated_look__consultation=consultation)
        .order_by("-created_at")
        .first()
    )

    if evolved is not None:
        return JsonResponse(
            {
                "completed": True,
                "status": "completed",
                "generated_image": evolved.evolved_image.url,
                "reasoning": evolved.reasoning,
                "added_items": evolved.added_items,
            }
        )

    job = (
        Job.objects
        .filter(
            consultation=consultation,
            job_type=JobType.STYLE_EVOLUTION,
        )
        .order_by("-created_at")
        .first()
    )

    if consultation.style_evolution_status == "failed":
        return JsonResponse(
            {
                "completed": False,
                "status": "failed",
                "message": (
                    job.error_message
                    if job and job.error_message
                    else "Style evolution failed."
                ),
            }
        )

    if job is None:
        return JsonResponse({"completed": False, "status": "pending"})

    if job.job_status == JobStatus.FAILED:
        return JsonResponse(
            {
                "completed": False,
                "status": "failed",
                "message": job.error_message or "Style evolution failed.",
            }
        )

    if job.job_status == JobStatus.COMPLETED:
        return JsonResponse(
            {
                "completed": False,
                "status": "failed",
                "message": (
                    "Style evolution finished, "
                    "but no evolved look was found."
                ),
            }
        )

    if job.job_status == JobStatus.RUNNING:
        return JsonResponse({"completed": False, "status": "processing"})

    return JsonResponse({"completed": False, "status": "pending"})


# ==========================================================
# Payments (Razorpay)
# ==========================================================

def sync_pending_payments(user):
    """
    Safety net: credit any recent 'created' payments that Razorpay
    has actually captured (e.g. the browser closed before verify).
    """

    client = razorpay_client()

    pending = Payment.objects.filter(
        user=user, status="created"
    ).order_by("-pk")[:5]

    for p in pending:
        try:
            result = client.order.payments(p.razorpay_order_id)
        except Exception:
            logger.exception("Payment sync failed for %s", p.razorpay_order_id)
            continue

        for item in result.get("items", []):
            if item.get("status") == "captured" and item.get("amount") == p.amount:
                with transaction.atomic():
                    locked = Payment.objects.select_for_update().get(pk=p.pk)
                    if locked.status != "paid":
                        locked.razorpay_payment_id = item.get("id")
                        locked.status = "paid"
                        locked.paid_at = timezone.now()
                        locked.save(
                            update_fields=[
                                "razorpay_payment_id",
                                "status",
                                "paid_at",
                            ]
                        )
                        CreditManager.add_credits(user, locked.credits)
                        logger.info(
                            "Payment sync credited order %s",
                            p.razorpay_order_id,
                        )
                break


def premium_pricing(request):
    if request.user.is_authenticated:
        sync_pending_payments(request.user)
    return render(request, "pricing.html")


@login_required
def create_razorpay_order(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "POST request required."},
            status=405,
        )

    plan_key = request.POST.get("plan")
    plan = RAZORPAY_PLANS.get(plan_key)

    if not plan:
        return JsonResponse(
            {"success": False, "message": "Invalid plan selected."},
            status=400,
        )

    try:
        client = razorpay_client()

        razorpay_order = client.order.create(
            {
                "amount": plan["amount"],
                "currency": "INR",
                "receipt": (
                    f"styriva_{request.user.id}_"
                    f"{timezone.now().timestamp()}"
                ),
            }
        )

        Payment.objects.create(
            user=request.user,
            plan=plan_key,
            amount=plan["amount"],
            credits=plan["credits"],
            razorpay_order_id=razorpay_order["id"],
            status="created",
        )

        return JsonResponse(
            {
                "success": True,
                "order_id": razorpay_order["id"],
                "amount": plan["amount"],
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "plan": plan_key,
                "credits": plan["credits"],
            }
        )

    except Exception as error:
        logger.exception("Razorpay order creation failed")
        return JsonResponse(
            {"success": False, "message": str(error)},
            status=500,
        )


@login_required
@transaction.atomic
def verify_razorpay_payment(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "POST request required."},
            status=405,
        )

    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse(
            {"success": False, "message": "Missing payment information."},
            status=400,
        )

    try:
        client = razorpay_client()

        payment = (
            Payment.objects
            .select_for_update()
            .get(
                razorpay_order_id=razorpay_order_id,
                user=request.user,
            )
        )

        # Prevent duplicate crediting
        if payment.status == "paid":
            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment already processed.",
                    "credits": request.user.profile.credits,
                }
            )

        # Verify Razorpay signature
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        # Fetch payment from Razorpay
        razorpay_payment = client.payment.fetch(razorpay_payment_id)

        # Payment must belong to this order
        if razorpay_payment.get("order_id") != razorpay_order_id:
            return JsonResponse(
                {"success": False, "message": "Payment/order mismatch."},
                status=400,
            )

        # Amount must match our database
        if razorpay_payment.get("amount") != payment.amount:
            return JsonResponse(
                {"success": False, "message": "Payment amount mismatch."},
                status=400,
            )

        # Only captured payments receive credits
        if razorpay_payment.get("status") != "captured":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payment has not been captured yet.",
                },
                status=400,
            )

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "paid"
        payment.paid_at = timezone.now()
        payment.save(
            update_fields=[
                "razorpay_payment_id",
                "razorpay_signature",
                "status",
                "paid_at",
            ]
        )

        CreditManager.add_credits(request.user, payment.credits)

        return JsonResponse(
            {
                "success": True,
                "message": f"{payment.credits} credits added successfully.",
                "credits": request.user.profile.credits,
            }
        )

    except Payment.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Payment order not found."},
            status=404,
        )

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse(
            {"success": False, "message": "Invalid payment signature."},
            status=400,
        )

    except Exception as error:
        logger.exception("Razorpay payment verification failed")
        return JsonResponse(
            {"success": False, "message": str(error)},
            status=500,
        )


@csrf_exempt
@require_POST
def razorpay_webhook(request):

    signature = request.headers.get("X-Razorpay-Signature", "")
    body = request.body.decode("utf-8")

    client = razorpay_client()

    try:
        client.utility.verify_webhook_signature(
            body, signature, settings.RAZORPAY_WEBHOOK_SECRET
        )
    except Exception:
        logger.warning("Razorpay webhook: invalid signature")
        return HttpResponse(status=400)

    event = json.loads(body)

    if event.get("event") not in ("payment.captured", "order.paid"):
        return HttpResponse(status=200)

    entity = event["payload"]["payment"]["entity"]
    order_id = entity.get("order_id")

    with transaction.atomic():

        payment = (
            Payment.objects
            .select_for_update()
            .filter(razorpay_order_id=order_id)
            .first()
        )

        if payment is None:
            logger.warning("Razorpay webhook: order %s not found", order_id)
            return HttpResponse(status=200)

        if payment.status == "paid":
            return HttpResponse(status=200)

        if entity.get("amount") != payment.amount:
            logger.warning("Razorpay webhook: amount mismatch for %s", order_id)
            return HttpResponse(status=200)

        payment.razorpay_payment_id = entity.get("id")
        payment.status = "paid"
        payment.paid_at = timezone.now()
        payment.save(update_fields=["razorpay_payment_id", "status", "paid_at"])

        CreditManager.add_credits(payment.user, payment.credits)

    logger.info("Razorpay webhook: credited order %s", order_id)
    return HttpResponse(status=200)


# ==========================================================
# STYLE MY PIECE - PROGRESSIVE GENERATION
# ==========================================================

def get_piece_for_request(request, piece_id):
    """
    Return a PieceStyling record only if it belongs to the
    authenticated user or the guest session.
    """

    piece = get_object_or_404(PieceStyling, pk=piece_id)

    if request.user.is_authenticated:
        if piece.user_id != request.user.id:
            return None

    else:
        allowed_ids = request.session.get("style_my_piece_ids", [])

        if piece.user_id is not None or piece.id not in allowed_ids:
            return None

    return piece


# ----------------------------------------------------------
# Upload clothing and start first look
# ----------------------------------------------------------

def style_my_piece(request):

    if request.method != "POST":
        return render(request, "style_my_piece.html")

    if is_rate_limited(request):
        return rate_limited_response()

    garment_image = request.FILES.get("garment_image")
    garment_type = request.POST.get("garment_type")

    if not garment_image or not garment_type:
        return JsonResponse(
            {
                "success": False,
                "message": "Please upload an image and select a clothing type.",
            },
            status=400,
        )

    allowed_types = [
        "top",
        "bottom",
        "dress",
        "outerwear",
        "shoes",
        "accessory",
        "other",
    ]

    if garment_type not in allowed_types:
        return JsonResponse(
            {
                "success": False,
                "message": "Please select a valid clothing type.",
            },
            status=400,
        )

    is_valid, message = MediaManager().validate_upload(garment_image)

    if not is_valid:
        return JsonResponse(
            {"success": False, "message": message},
            status=400,
        )

    try:
        with transaction.atomic():

            piece = PieceStyling.objects.create(
                user=request.user if request.user.is_authenticated else None,
                garment_image=garment_image,
                garment_type=garment_type,
                occasion=request.POST.get("occasion", ""),
                style_preference=request.POST.get("style_preference", ""),
            )

            # Automatically queue the first look (free batch 0).
            job = JobQueue.create_piece_styling_job(
                piece,
                payload={
                    "look_number": 1,
                    "batch_number": 0,
                },
            )

        # Allow the guest session to access its own piece.
        if not request.user.is_authenticated:
            allowed_ids = request.session.get("style_my_piece_ids", [])
            allowed_ids.append(piece.id)
            request.session["style_my_piece_ids"] = allowed_ids
            request.session.modified = True

        return JsonResponse(
            {
                "success": True,
                "message": (
                    "Your clothing piece has been uploaded. "
                    "Your first look is starting!"
                ),
                "status": "processing",
                "piece_id": piece.id,
                "job_id": job.id,
                "next_look_number": 1,
            }
        )

    except Exception:
        logger.exception("Style My Piece upload or job creation failed")
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "We couldn't save your clothing image or start "
                    "styling. Please try again."
                ),
            },
            status=500,
        )


# ----------------------------------------------------------
# Check Style My Piece generation status
# ----------------------------------------------------------


def piece_styling_status(request, piece_id):

    piece = get_piece_for_request(request, piece_id)

    if piece is None:
        return JsonResponse(
            {"success": False, "message": "Styling session not found."},
            status=404,
        )

    results = piece.results.order_by("order")

    result_data = [
        {
            "id": result.id,
            "title": result.title,
            "description": result.description,
            "image_url": (
                result.generated_image.url
                if result.generated_image else None
            ),
            "order": result.order,
        }
        for result in results
    ]

    piece_jobs = Job.objects.filter(
        piece_styling=piece,
        job_type=JobType.PIECE_STYLING,
    )

    latest_job = piece_jobs.order_by("-created_at").first()

    active_job = piece_jobs.filter(
        job_status__in=[
            JobStatus.PENDING,
            JobStatus.RUNNING,
        ],
    ).exists()

    if active_job:
        status = "processing"
    elif latest_job and latest_job.job_status == JobStatus.FAILED:
        status = "failed"
    elif result_data:
        status = "completed"
    else:
        status = piece.status

    next_number = piece.next_look_number

    if request.user.is_authenticated:
        credits_remaining = request.user.profile.credits
    else:
        credits_remaining = 0

    next_requires_signup = (
        next_number > FREE_PIECE_LOOKS
        and not request.user.is_authenticated
    )

    next_requires_credit = (
        next_number > FREE_PIECE_LOOKS
    )

    return JsonResponse(
        {
            "success": True,
            "piece_id": piece.id,
            "status": status,
            "completed": status == "completed",
            "processing": active_job,
            "results": result_data,
            "look_count": len(result_data),
            "next_look_number": next_number,

            # Number of free looks still available.
            "remaining_looks": max(
                0,
                FREE_PIECE_LOOKS - len(result_data),
            ),

            "next_requires_credit": next_requires_credit,
            "next_requires_signup": next_requires_signup,
            "credits_remaining": credits_remaining,
            "credits_required": (
                1 if next_requires_credit else 0
            ),
            "can_generate_more": not active_job,

            "message": (
                latest_job.error_message
                if status == "failed" and latest_job
                else ""
            ),
        }
    )


@require_POST
def generate_next_piece_look(request, piece_id):

    if is_rate_limited(request):
        return rate_limited_response()

    piece = get_piece_for_request(request, piece_id)

    if piece is None:
        return JsonResponse(
            {
                "success": False,
                "message": "Styling session not found.",
            },
            status=404,
        )

    try:
        expected_number = int(
            request.POST.get("expected_look_number", "")
        )

        if expected_number < 1:
            raise ValueError

        with transaction.atomic():

            locked_piece = (
                PieceStyling.objects
                .select_for_update()
                .get(pk=piece.id)
            )

            # Prevent duplicate or outdated requests.
            if expected_number != locked_piece.next_look_number:
                return JsonResponse(
                    {
                        "success": False,
                        "status": locked_piece.status,
                        "message": "Please refresh your results.",
                        "next_look_number": locked_piece.next_look_number,
                    },
                    status=409,
                )

            # First six looks are free for everyone.
            # Look seven onward requires an account.
            if (
                expected_number > FREE_PIECE_LOOKS
                and not request.user.is_authenticated
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "requires_signup": True,
                        "redirect_url": reverse("signup"),
                        "message": (
                            "Create an account to generate "
                            "more looks."
                        ),
                    },
                    status=403,
                )

            # Make sure no other look is currently processing.
            existing_active_job = Job.objects.filter(
                piece_styling=locked_piece,
                job_type=JobType.PIECE_STYLING,
                job_status__in=[
                    JobStatus.PENDING,
                    JobStatus.RUNNING,
                ],
            ).first()

            if existing_active_job:
                return JsonResponse(
                    {
                        "success": True,
                        "status": "processing",
                        "job_id": existing_active_job.id,
                        "look_number": expected_number,
                        "message": (
                            "Your look is already being generated."
                        ),
                    }
                )

            # Every look after the first six costs one credit.
            if expected_number > FREE_PIECE_LOOKS:

                # Extra ownership protection.
                if locked_piece.user_id != request.user.id:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Account mismatch.",
                        },
                        status=403,
                    )

                # Check whether this exact look was already paid for.
                # This prevents charging twice when a failed job
                # is retried.
                already_charged = Job.objects.filter(
                    piece_styling=locked_piece,
                    job_type=JobType.PIECE_STYLING,
                    payload__look_number=expected_number,
                    payload__credit_charged=True,
                ).exists()

                if not already_charged:

                    credit_result = (
                        CreditManager.consume_piece_generation(
                            request.user
                        )
                    )

                    if credit_result is None:
                        return JsonResponse(
                            {
                                "success": False,
                                "requires_upgrade": True,
                                "credits_required": 1,
                                "credits_remaining": (
                                    request.user.profile.credits
                                ),
                                "message": (
                                    "You need one credit to "
                                    "generate this look."
                                ),
                            },
                            status=403,
                        )

                else:
                    credit_result = request.user.profile.credits

            else:
                credit_result = (
                    request.user.profile.credits
                    if request.user.is_authenticated
                    else 0
                )

            # Queue exactly one look.
            # The transaction also rolls back the credit deduction
            # if job creation fails.
            job = JobQueue.create_piece_styling_job(
                locked_piece,
                payload={
                    "look_number": expected_number,
                    "credit_charged": (
                        expected_number > FREE_PIECE_LOOKS
                    ),
                },
            )

            locked_piece.status = "processing"
            locked_piece.save(
                update_fields=["status"]
            )

        return JsonResponse(
            {
                "success": True,
                "status": "processing",
                "job_id": job.id,
                "look_number": expected_number,
                "credits_remaining": credit_result,
                "message": "Your next look is being generated!",
            }
        )

    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "message": "A valid look number is required.",
            },
            status=400,
        )

    except Exception:
        logger.exception(
            "Next Style My Piece look generation failed"
        )

        return JsonResponse(
            {
                "success": False,
                "message": (
                    "We couldn't start your next look. "
                    "Please try again."
                ),
            },
            status=500,
        )

# ==========================================================
# Static / Informational Pages
# ==========================================================

def privacy_policy(request):
    return render(request, "privacy.html")


def terms(request):
    return render(request, "terms.html")


def contact(request):
    return render(request, "contact.html")


def about_view(request):
    return render(request, "about.html")


def how_it_works_view(request):
    return render(request, "how_it_works.html")


def guides_view(request):
    return render(request, "guides.html")


def faq_view(request):
    return render(request, "faq.html")


def cookies_view(request):
    return render(request, "cookies.html")


def disclaimer_view(request):
    return render(request, "disclaimer.html")