from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required

import razorpay

from .models import (
    StyleConsultation,
    GeneratedLook,
    EvolvedLook,
)

from jobs.queue import JobQueue
from jobs.models import Job
from jobs.constants import (
    JobStatus,
    JobType,
)

from media_manager.manager import MediaManager

from accounts.services import CreditManager
from accounts.models import Payment, UserUsage

from .abuse_protection import is_rate_limited

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging
logger = logging.getLogger(__name__)


RAZORPAY_PLANS = {
    "starter": {
        "name": "Starter",
        "amount": 19900,
        "credits": 20,
    },
    "premium": {
        "name": "Premium",
        "amount": 39900,
        "credits": 50,
    },
    "creator": {
        "name": "Creator",
        "amount": 69900,
        "credits": 100,
    },
}

# ==========================================================
# Splash
# ==========================================================

def splash(request):

    return render(
        request,
        "splash.html"
    )


# ==========================================================
# Generate Style Look
# ==========================================================

def generate_style_look(request):

    if request.method == "POST":

        # ==================================================
        # ABUSE PROTECTION
        # ==================================================

        if is_rate_limited(request):

            return JsonResponse(
                {
                    "success": False,
                    "rate_limited": True,
                    "message": (
                        "Too many requests. "
                        "Please wait a moment and try again."
                    ),
                },
                status=429,
            )

        # ==================================================
        # Complimentary Guest Session Check
        # ==================================================

        if not request.user.is_authenticated:

            free_generation_used = request.session.get(
                "free_generation_used",
                False
            )

            if free_generation_used:

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

        # ==================================================
        # Authenticated User Credit Check
        # ==================================================

        if request.user.is_authenticated:

            if not CreditManager.can_generate(
                request.user
            ):

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

        # ==================================================
        # STEP 1
        # Collect uploaded images
        #
        # Only the user's own photo is required.
        # Tops, bottoms, one-pieces, shoes and scarves are
        # all optional, but at least ONE garment (top,
        # bottom or one-piece) is needed.
        # ==================================================

        required_files = {
            "user_model_photo": request.FILES.get(
                "user_model_photo"
            ),
        }

        optional_files = {}

        for prefix in ("top", "bottom", "dress", "shoe", "scarf"):
            for i in range(1, 4):
                field = f"{prefix}_{i}"
                optional_files[field] = request.FILES.get(field)

        uploaded_files = {
            **required_files,
            **optional_files,
        }

        # ==================================================
        # STEP 2
        # Check required image + at least one garment
        # ==================================================

        if required_files["user_model_photo"] is None:

            return JsonResponse(
                {
                    "success": False,
                    "message": "Please upload your photo.",
                },
                status=400,
            )

        garment_fields = [
            f"{prefix}_{i}"
            for prefix in ("top", "bottom", "dress")
            for i in range(1, 4)
        ]

        has_garment = any(
            uploaded_files[field] is not None
            for field in garment_fields
        )

        if not has_garment:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Please upload at least one top, "
                        "bottom or one-piece."
                    ),
                },
                status=400,
            )

        # ==================================================
        # STEP 3
        # Validate uploaded images
        # ==================================================

        media_manager = MediaManager()

        for field_name, uploaded_file in uploaded_files.items():

            if uploaded_file is None:
                continue

            try:

                is_valid, message = (
                    media_manager.validate_upload(
                        uploaded_file
                    )
                )

            except Exception as error:

                return JsonResponse(
                    {
                        "success": False,
                        "message": (
                            "We could not validate "
                            f"{field_name.replace('_', ' ')}. "
                            f"Error: {str(error)}"
                        )
                    },
                    status=400,
                )

            if not is_valid:

                return JsonResponse(
                    {
                        "success": False,
                        "message": (
                            f"Invalid "
                            f"{field_name.replace('_', ' ')}: "
                            f"{message}"
                        )
                    },
                    status=400,
                )

        # ==================================================
        # STEP 4
        # Create Style Consultation
        # ==================================================

        try:

            consultation = StyleConsultation.objects.create(

                user=(
                    request.user
                    if request.user.is_authenticated
                    else None
                ),

                gender=request.POST.get("gender"),

                occasion=request.POST.get("occasion"),

                vibe=request.POST.get("vibe"),

                weather=request.POST.get("weather"),

                user_model_photo=uploaded_files["user_model_photo"],

                # tops, bottoms, one-pieces, shoes, scarves
                # (any that were not uploaded are saved as empty)
                **optional_files,
            )

        except Exception as error:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "We could not create your "
                        "style consultation. "
                        f"Error: {str(error)}"
                    )
                },
                status=500,
            )

        # ==================================================
        # STEP 5
        # Create background generation job
        # ==================================================

        try:

            JobQueue.create_style_generation_job(
                consultation
            )

            # ==============================================
            # SPEND CREDIT / MARK COMPLIMENTARY SESSION USED
            # ==============================================

            if request.user.is_authenticated:

                CreditManager.consume_generation(
                    request.user
                )

        except Exception as error:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Your images were uploaded, "
                        "but we could not start "
                        "style generation. "
                        f"Error: {str(error)}"
                    )
                },
                status=500,
            )

        # ==================================================
        # STEP 6
        # Redirect to loading/result page
        # ==================================================

        return JsonResponse(
            {
                "success": True,
                "redirect_url": reverse(
                    "result_view",
                    kwargs={
                        "consultation_id": consultation.id
                    }
                )
            }
        )

    return render(
        request,
        "generate_style_look.html"
    )


# ==========================================================
# Result View
# ==========================================================
def result_view(
    request,
    consultation_id
):

    consultation = get_object_or_404(
        StyleConsultation,
        id=consultation_id
    )

    generated_look = (
        GeneratedLook.objects
        .filter(
            consultation=consultation
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    # ======================================================
    # Guest has successfully completed their complimentary
    # styling session
    # ======================================================

    if (
        generated_look is not None
        and not request.user.is_authenticated
    ):
        request.session["free_generation_used"] = True
        request.session.modified = True

    if not generated_look:

        return render(
            request,
            "loading.html",
            {
                "consultation": consultation,
            }
        )

    return render(
        request,
        "result.html",
        {
            "consultation": consultation,
            "generated_look": generated_look,
        }
    )


# ==========================================================
# Generate Style Evolution
# ==========================================================

def generate_style_evolution(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "POST request required."
            },
            status=405
        )

    # ==================================================
    # ABUSE PROTECTION
    # ==================================================

    if is_rate_limited(request):

        return JsonResponse(
            {
                "success": False,
                "rate_limited": True,
                "message": (
                    "Too many requests. "
                    "Please wait a moment and try again."
                ),
            },
            status=429,
        )

    # ==================================================
    # Complimentary Guest Session Check
    # ==================================================

    if not request.user.is_authenticated:

        free_evolution_used = request.session.get(
            "free_evolution_used",
            False
        )

        if free_evolution_used:
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

        consultation_id = request.POST.get(
            "consultation_id"
        )

        style_preference = request.POST.get(
            "style_preference",
            "minimal"
        )

        extras = request.POST.getlist(
            "extras[]"
        )

        consultation = get_object_or_404(
            StyleConsultation,
            id=consultation_id
        )

        consultation.style_evolution_status = (
            "processing"
        )

        consultation.save(
            update_fields=[
                "style_evolution_status"
            ]
        )

        JobQueue.create_style_evolution_job(
            consultation=consultation,
            style_preference=style_preference,
            extras=extras,
        )

        # ==================================================
        # MARK COMPLIMENTARY SESSION USED / SPEND CREDIT
        # ==================================================

        if not request.user.is_authenticated:

            request.session["free_evolution_used"] = True
            request.session.modified = True

        else:
            CreditManager.consume_style_evolution(
                request.user
            )

        return JsonResponse(
            {
                "success": True,
                "status": "processing",
            }
        )

    except Exception as error:

        if consultation is not None:

            consultation.style_evolution_status = (
                "failed"
            )

            consultation.save(
                update_fields=[
                    "style_evolution_status"
                ]
            )

        return JsonResponse(
            {
                "success": False,
                "status": "failed",
                "message": str(error),
            },
            status=500
        )


# ==========================================================
# Generation Status
# ==========================================================

def generation_status(
    request,
    consultation_id
):

    consultation = get_object_or_404(
        StyleConsultation,
        id=consultation_id
    )

    generated_look = (
        GeneratedLook.objects
        .filter(
            consultation=consultation
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if generated_look is not None:

        return JsonResponse({
            "completed": True,
            "status": "completed",
        })

    job = (
        Job.objects
        .filter(
            consultation=consultation,
            job_type=JobType.STYLE_GENERATION,
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if job is None:

        return JsonResponse({
            "completed": False,
            "status": "pending",
        })

    if job.job_status == JobStatus.FAILED:

        return JsonResponse({
            "completed": False,
            "status": "failed",
            "message": (
                job.error_message
                or
                "Style generation failed."
            ),
        })

    if job.job_status == JobStatus.COMPLETED:

        return JsonResponse({
            "completed": False,
            "status": "failed",
            "message": (
                "Style generation finished, "
                "but no generated look was found."
            ),
        })

    if job.job_status == JobStatus.RUNNING:

        return JsonResponse({
            "completed": False,
            "status": "processing",
        })

    return JsonResponse({
        "completed": False,
        "status": "pending",
    })


# ==========================================================
# Style Evolution Status
# ==========================================================

def style_evolution_status(
    request,
    consultation_id
):

    consultation = get_object_or_404(
        StyleConsultation,
        id=consultation_id
    )

    evolved = (
        EvolvedLook.objects
        .filter(
            generated_look__consultation=consultation
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if evolved is not None:

        return JsonResponse({
            "completed": True,
            "status": "completed",
            "generated_image": evolved.evolved_image.url,
            "reasoning": evolved.reasoning,
            "added_items": evolved.added_items,
        })

    job = (
        Job.objects
        .filter(
            consultation=consultation,
            job_type=JobType.STYLE_EVOLUTION,
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if (
        consultation.style_evolution_status
        == "failed"
    ):

        return JsonResponse({
            "completed": False,
            "status": "failed",
            "message": (
                job.error_message
                if job
                and job.error_message
                else
                "Style evolution failed."
            ),
        })

    if job is None:

        return JsonResponse({
            "completed": False,
            "status": "pending",
        })

    if job.job_status == JobStatus.FAILED:

        return JsonResponse({
            "completed": False,
            "status": "failed",
            "message": (
                job.error_message
                or
                "Style evolution failed."
            ),
        })

    if job.job_status == JobStatus.COMPLETED:

        return JsonResponse({
            "completed": False,
            "status": "failed",
            "message": (
                "Style evolution finished, "
                "but no evolved look was found."
            ),
        })

    if job.job_status == JobStatus.RUNNING:

        return JsonResponse({
            "completed": False,
            "status": "processing",
        })

    return JsonResponse({
        "completed": False,
        "status": "pending",
    })


# ==========================================================
# Static / Informational Pages
# ==========================================================

def premium_pricing(request):
    return render(request, "pricing.html")


@login_required
def create_razorpay_order(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST request required.",
            },
            status=405,
        )

    plan_key = request.POST.get("plan")

    plan = RAZORPAY_PLANS.get(plan_key)

    if not plan:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid plan selected.",
            },
            status=400,
        )

    try:

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

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

        payment = Payment.objects.create(
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

        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=500,
        )


@login_required
@transaction.atomic
def verify_razorpay_payment(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST request required.",
            },
            status=405,
        )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    if not all(
        [
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature,
        ]
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Missing payment information.",
            },
            status=400,
        )

    try:

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

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
        razorpay_payment = client.payment.fetch(
            razorpay_payment_id
        )

        # Make sure payment belongs to this order
        if (
            razorpay_payment.get("order_id")
            != razorpay_order_id
        ):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payment/order mismatch.",
                },
                status=400,
            )

        # Make sure amount matches our database
        if (
            razorpay_payment.get("amount")
            != payment.amount
        ):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payment amount mismatch.",
                },
                status=400,
            )

        # Only captured payments receive credits
        if razorpay_payment.get("status") != "captured":
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Payment has not been captured yet."
                    ),
                },
                status=400,
            )

        # Mark payment as paid
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

        # Add purchased credits
        CreditManager.add_credits(
            request.user,
            payment.credits,
        )

        return JsonResponse(
            {
                "success": True,
                "message": (
                    f"{payment.credits} credits "
                    "added successfully."
                ),
                "credits": request.user.profile.credits,
            }
        )

    except Payment.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "message": "Payment order not found.",
            },
            status=404,
        )

    except razorpay.errors.SignatureVerificationError:

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid payment signature.",
            },
            status=400,
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "message": str(error),
            },
            status=500,
        )
        
        
@csrf_exempt
@require_POST
def razorpay_webhook(request):

    signature = request.headers.get("X-Razorpay-Signature", "")
    body = request.body.decode("utf-8")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

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
        payment.save(
            update_fields=["razorpay_payment_id", "status", "paid_at"]
        )

        CreditManager.add_credits(payment.user, payment.credits)

    logger.info("Razorpay webhook: credited order %s", order_id)
    return HttpResponse(status=200)

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