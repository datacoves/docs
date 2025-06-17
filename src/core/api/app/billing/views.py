import json
import logging
from collections import OrderedDict

import stripe
from billing import manager  # noqa: F401. Imported to configure stripe.
from billing.serializers import AccountSubscriptionSerializer
from core.mixins.views import VerboseCreateModelMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class SubscribeAccount(VerboseCreateModelMixin, generics.CreateAPIView):
    serializer_class = AccountSubscriptionSerializer
    permission_classes = [IsAuthenticated]


@api_view(("POST",))
@renderer_classes((JSONRenderer,))
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None
    try:
        if webhook_secret:
            signature = request.headers.get("Stripe-Signature")
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        else:
            logging.warning(
                "stripe_webhook: won't verify request, STRIPE_WEBHOOK_SECRET not set."
            )
            # The rest of this block is the stripe.Webhook.construct_event source
            # code without the line that does signature verification.
            if hasattr(payload, "decode"):
                payload = payload.decode("utf-8")
            data = json.loads(payload, object_pairs_hook=OrderedDict)
            event = stripe.Event.construct_from(data, stripe.api_key)
    except ValueError:
        logging.error("stripe_webhook: bad request")
        return Response(status=400)
    except stripe.error.SignatureVerificationError:
        logging.error("stripe_webhook: signature verification error")
        return Response(status=400)

    # Seems like too much data to save it all, and too little context to
    # decide what is relevant. Let each handlers do the logging instead.
    # log_stripe_event(type=event.type, id=event.id, **event.data)

    handler = getattr(manager, "handle_" + event.type.replace(".", "_"), None)
    if not handler:
        # log_stripe_event(type=event.type, data=event.data, id=event.id, handled=False)
        # TODO: It doesn't seem wise to respond OK to all events without
        # handling them. Uncomment the following line and fix the consequences.
        # Configure stripe so we don't get sent the webhooks we don't care about.
        return Response({}, status=501)
        # return Response({"status": "success"})
    response = handler(event)
    # So that handlers don't have to return responses if they don't care.
    response = response or Response({"status": "success"})
    response = Response(response) if isinstance(response, dict) else response
    return response
