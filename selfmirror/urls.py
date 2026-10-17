from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.splash,
        name="splash"
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

path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),

]