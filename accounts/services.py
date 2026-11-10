
from django.db import transaction

from .models import Profile, UserUsage


class CreditManager:

    @staticmethod
    @transaction.atomic
    def can_generate(user):
        """
        Checks whether the user can generate a style.
        """

        usage = user.usage
        profile = user.profile

        if not usage.signup_free_used:
            return True

        if profile.credits > 0:
            return True

        return False

    @staticmethod
    @transaction.atomic
    def consume_generation(user):
        """
        Consumes one normal style generation.

        Priority:
        1. Free signup generation
        2. Purchased credit
        """

        usage = user.usage
        profile = user.profile

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

        if profile.credits > 0:

            profile.credits -= 1

            profile.save(
                update_fields=["credits"]
            )

            usage.total_generations += 1

            usage.save(
                update_fields=["total_generations"]
            )

            return "credit"

        return None

    @staticmethod
    @transaction.atomic
    def can_evolve(user):
        """
        Checks whether the user has credits
        for Style Evolution.
        """

        profile = user.profile

        return profile.credits > 0

    @staticmethod
    @transaction.atomic
    def consume_style_evolution(user):
        """
        Consumes one credit for Style Evolution.
        """

        profile = user.profile
        usage = user.usage

        if profile.credits <= 0:
            return None

        profile.credits -= 1

        profile.save(
            update_fields=["credits"]
        )

        usage.total_style_evolutions += 1

        usage.save(
            update_fields=["total_style_evolutions"]
        )

        return "credit"

    @staticmethod
    @transaction.atomic
    def consume_piece_generation(user):
        """
        Consumes exactly ONE credit for ONE
        additional Style My Piece look.

        Does not consume the signup free generation.

        Returns:
            Remaining credits if successful.
            None if the user has no credits.
        """

        if not user or not user.is_authenticated:
            return None

        profile = (
            Profile.objects
            .select_for_update()
            .get(user=user)
        )

        if profile.credits <= 0:
            return None

        profile.credits -= 1

        profile.save(
            update_fields=["credits"]
        )

        usage = (
            UserUsage.objects
            .select_for_update()
            .get(user=user)
        )

        usage.total_generations += 1

        usage.save(
            update_fields=["total_generations"]
        )

        return profile.credits

    @staticmethod
    @transaction.atomic
    def add_credits(user, amount):
        """
        Adds purchased credits.
        """

        profile = (
            Profile.objects
            .select_for_update()
            .get(user=user)
        )

        profile.credits += amount

        profile.save(
            update_fields=["credits"]
        )

        return profile.credits
