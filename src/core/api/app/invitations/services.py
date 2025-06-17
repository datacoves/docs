from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_str


class EmailSender:
    @classmethod
    def _render_mail(cls, template_prefix, email, context, subject=None):
        """
        Renders an e-mail to `email`.  `template_prefix` identifies the
        e-mail that is to be sent, e.g. "account/email/email_confirmation"
        """
        if not subject:
            subject = render_to_string(f"{template_prefix}_subject.txt", context)
            # remove superfluous line breaks
            subject = " ".join(subject.splitlines()).strip()
        subject = force_str(subject)
        if isinstance(email, str):
            to = [email]
        else:
            to = email

        bodies = {}
        for ext in ["html", "txt"]:
            try:
                template_name = f"{template_prefix}_message.{ext}"
                bodies[ext] = render_to_string(template_name, context).strip()
            except TemplateDoesNotExist:
                if ext == "txt" and not bodies:
                    # We need at least one body
                    raise
        msg = cls.create_mail_message(
            subject,
            to,
            settings.DEFAULT_FROM_EMAIL,
            body_txt=bodies.get("txt"),
            body_html=bodies.get("html"),
        )
        return msg

    @classmethod
    def send_mail(cls, template_prefix, email, context, subject=None):
        msg = cls._render_mail(template_prefix, email, context, subject=subject)
        msg.send()

    @staticmethod
    def create_mail_message(
        subject,
        to,
        from_email=settings.DEFAULT_FROM_EMAIL,
        body_txt=None,
        body_html=None,
    ):
        if body_txt:
            msg = EmailMultiAlternatives(subject, body_txt, from_email, to)
            if body_html:
                msg.attach_alternative(body_html, "text/html")
        else:
            msg = EmailMessage(subject, body_html, from_email, to)
            msg.content_subtype = "html"  # Main content is now text/html
        return msg
