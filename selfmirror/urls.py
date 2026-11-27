from django.urls import path
from . import views

from django.contrib.staticfiles import finders
from django.http import HttpResponse, Http404


def serve_service_worker(request):
    worker_path = finders.find("service-worker.js")

    if not worker_path:
        raise Http404("Service worker not found")

    with open(worker_path, "r", encoding="utf-8") as file:
        response = HttpResponse(
            file.read(),
            content_type="application/javascript"
        )

    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"

    return response

urlpatterns = [
    
    path(
    "sw.js",
    serve_service_worker,
    name="service_worker"
),

    path(
        "",
        views.splash,
        name="splash"
    ),
    path(
    "choose/",
    views.choose_feature,
    name="choose_feature"
),
    path(
    "style-my-piece/",
    views.style_my_piece,
    name="style_my_piece"
),

    path(
        "generate/",
        views.generate_style_look,
        name="generate_style_look"
    ),

    path(
        "result/<int:consultation_id>/",
        views.result_view,
        name="result_view"
    ),
    
   
    path(
    "style-evolution/",
    views.generate_style_evolution,
    name="StyleEvolution",
),
    path(
    "generation-status/<int:consultation_id>/",
    views.generation_status,
    name="generation_status",
),

path(
    "style-evolution-status/<int:consultation_id>/",
    views.style_evolution_status,
    name="style_evolution_status",
),


path("premium/", views.premium_pricing, name="premium"),
path("payment-status/", views.payment_status, name="payment_status"),



path(
    "privacy/",
    views.privacy_policy,
    name="privacy_policy",
),

path(
    "terms/",
    views.terms,
    name="terms",
),

path(
    "contact/",
    views.contact,
    name="contact",
),

path(
    "about/",
    views.about_view,
    name="about",
),
path(
    "how-it-works/",
    views.how_it_works_view,
    name="how_it_works",
),

path(
    "guides/",
    views.guides_view,
    name="guides",
),


path(
    "faq/",
    views.faq_view,
    name="faq",
),

path(
    "cookies/",
    views.cookies_view,
    name="cookies",
),

path(
    "disclaimer/",
    views.disclaimer_view,
    name="disclaimer",
),

path(
    "payment/create-order/",
    views.create_razorpay_order,
    name="create_razorpay_order",
),

path(
    "payment/verify/",
    views.verify_razorpay_payment,
    name="verify_razorpay_payment",
),

path("payment/callback/", views.razorpay_callback, name="razorpay_callback"),

path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),

path(
    "style-my-piece/<int:piece_id>/status/",
    views.piece_styling_status,
    name="piece_styling_status",
),
path(
    "style-my-piece/<int:piece_id>/next/",
    views.generate_next_piece_look,
    name="generate_next_piece_look",
),

path("offline/", views.offline_view, name="offline"),

]