from django.db import transaction

from .models import Profile, UserUsage


class CreditManager:

    @staticmethod
    @transaction.atomic
    def can_generate(user):
        """
        Returns True if the authenticated user
        can generate a style.
        """

        usage = user.usage
        profile = user.profile

        # Free signup generation
        if not usage.signup_free_used:
            return True

        # Purchased credits
        if profile.credits > 0:
            return True

        return False

    @staticmethod
    @transaction.atomic
    def consume_generation(user):
        """
        Consumes one successful generation.

        Priority:
        1. Free signup generation
        2. Purchased credit
        """

        usage = user.usage
        profile = user.profile

        # Free signup generation
        if not usage.signup_free_used:

            usage.signup_free_used = True
            usage.total_generations += 1

            usage.save(
                update_fields=[
                    "signup_free_used",
                    "total_generations",
                ]
            )

            return "signup"

        # Purchased credit
        if profile.credits > 0:

            profile.credits -= 1

            profile.save(
                update_fields=[
                    "credits",
                ]
            )

            usage.total_generations += 1

            usage.save(
                update_fields=[
                    "total_generations",
                ]
            )

            return "credit"

        return None

    @staticmethod
    @transaction.atomic
    def can_evolve(user):
        """
        Returns True if the user has credits
        available for Style Evolution.
        """

        profile = user.profile

        return profile.credits > 0

    @staticmethod
    @transaction.atomic
    def consume_style_evolution(user):
        """
        Consumes one credit for a successful
        Style Evolution.
        """

        profile = user.profile
        usage = user.usage

        if profile.credits <= 0:
            return None

        profile.credits -= 1

        profile.save(
            update_fields=[
                "credits",
            ]
        )

        usage.total_style_evolutions += 1

        usage.save(
            update_fields=[
                "total_style_evolutions",
            ]
        )

        return "credit"

    @staticmethod
    @transaction.atomic
    def add_credits(user, amount):
        """
        Adds purchased credits.
        """

        profile = user.profile

        profile.credits += amount

        profile.save(
            update_fields=[
                "credits",
            ]
        )

        return profile.credits