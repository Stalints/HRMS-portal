from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Invoice, TicketComment, SupportTicket
from hr.models import Notification, NotificationType

@receiver(post_save, sender=Task)
def notify_task_assignment(sender, instance, created, **kwargs):
    if created and instance.assigned_to:
        Notification.objects.create(
            user=instance.assigned_to,
            title="New Task Assigned",
            message=f"You have been assigned to task: '{instance.title}' for project '{instance.project.name}'.",
            type=NotificationType.EVENT
        )

@receiver(post_save, sender=Invoice)
def notify_invoice_generated(sender, instance, created, **kwargs):
    if created and instance.project and instance.project.client and instance.project.client.user:
        Notification.objects.create(
            user=instance.project.client.user,
            title="New Invoice Generated",
            message=f"A new invoice #{instance.id} for project '{instance.project.name}' has been generated with amount {instance.total_amount}.",
            type=NotificationType.ANNOUNCEMENT
        )

@receiver(post_save, sender=TicketComment)
def notify_ticket_reply(sender, instance, created, **kwargs):
    if created:
        ticket = instance.ticket
        # If the reply is by the client user, notify the assigned_to HR
        if instance.author == ticket.client.user:
            if ticket.assigned_to:
                Notification.objects.create(
                    user=ticket.assigned_to,
                    title="New Reply on Ticket",
                    message=f"Client replied on ticket '{ticket.title}'.",
                    type=NotificationType.EVENT
                )
        else:
            # If the reply is by HR/Admin, notify the client user
            Notification.objects.create(
                user=ticket.client.user,
                title="New Reply on Ticket",
                message=f"Support replied on your ticket '{ticket.title}'.",
                type=NotificationType.EVENT
            )
