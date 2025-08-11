from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, Prefetch
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, Http404
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from .models import Message, Conversation, MessageAttachment
from .forms import MessageForm


@login_required
def api_unread_count(request):
    count = Message.objects.filter(
        recipient=request.user, is_read=False, deleted_by_recipient=False
    ).count()
    return JsonResponse({"unread": count})


@login_required
def api_inbox_latest(request):
    """
    Latest 10 messages to/from the user (excluding items the user deleted).
    Optional ?since=ISO-8601 to only return newer ones.
    """
    qs = (
        Message.objects
        .filter(
            (Q(sender=request.user) & Q(deleted_by_sender=False)) |
            (Q(recipient=request.user) & Q(deleted_by_recipient=False))
        )
        .select_related('sender', 'recipient')
        .order_by('-sent_at')
    )

    since = request.GET.get('since')
    if since:
        dt = parse_datetime(since)
        if dt is None:
            return HttpResponseBadRequest("Invalid 'since'")
        if dt.tzinfo is None:
            dt = make_aware(dt)
        qs = qs.filter(sent_at__gt=dt)

    data = [{
        "id": m.pk,
        "subject": m.subject or "(no subject)",
        "snippet": (m.body or "")[:140],
        "sender": m.sender.get_full_name() or m.sender.username,
        "recipient": m.recipient.get_full_name() or m.recipient.username,
        "is_read": m.is_read,
        "importance": m.importance,
        "sent_at": m.sent_at.isoformat(),
        "detail_url": request.build_absolute_uri(reverse("message_detail", args=[m.pk])),
    } for m in qs[:10]]

    return JsonResponse({"messages": data})


@login_required
@require_POST
def api_mark_read(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if msg.recipient_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    if not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=['is_read'])
    return JsonResponse({"ok": True})



def _get_or_create_conversation(user_a, user_b):
    """Return an existing 2‑party conversation or create a new one."""
    convo = (
        Conversation.objects
        .filter(participants=user_a)
        .filter(participants=user_b)
        .first()
    )
    if not convo:
        convo = Conversation.objects.create()
        convo.participants.add(user_a, user_b)
    return convo


@login_required
def inbox(request):
    """
    One card per conversation using each convo’s latest visible message
    (i.e., not soft-deleted for the current user), ordered by last activity.
    """
    query = request.GET.get('q', '')

    conversations = (
        Conversation.objects.filter(participants=request.user)
        .prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects
                    .select_related('sender', 'recipient')
                    .filter(
                        (Q(sender=request.user) & Q(deleted_by_sender=False)) |
                        (Q(recipient=request.user) & Q(deleted_by_recipient=False))
                    )
                    .order_by('-sent_at')
            ),
            'participants',
        )
    )

    latest_messages = []
    for convo in conversations:
        last_msg = next(iter(convo.messages.all()), None)
        if last_msg:
            latest_messages.append(last_msg)

    if query:
        q = query.strip()
        latest_messages = [
            m for m in latest_messages
            if (q.lower() in (m.subject or '').lower())
            or (q.lower() in (m.body or '').lower())
            or any(q.lower() in (p.first_name or '').lower()
                   or q.lower() in (p.last_name or '').lower()
                   or q.lower() in (p.username or '').lower()
                   for p in convo.participants.all())
        ]

    latest_messages.sort(key=lambda m: m.sent_at, reverse=True)

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False, deleted_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'conversations': conversations,
        'messages': latest_messages,
        'active_tab': 'inbox',
        'unread_count': unread_count,
        'query': query,
    })


@login_required
def all_messages(request):
    """Flat list of all messages to/from the user (excluding soft-deleted ones for this user)."""
    query = request.GET.get('q', '')

    messages_qs = (
        Message.objects
        .filter(
            (Q(sender=request.user) & Q(deleted_by_sender=False)) |
            (Q(recipient=request.user) & Q(deleted_by_recipient=False))
        )
        .select_related('sender', 'recipient', 'conversation')
        .order_by('-sent_at')
    )

    if query:
        messages_qs = messages_qs.filter(Q(subject__icontains=query) | Q(body__icontains=query))

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False, deleted_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'all',
        'unread_count': unread_count,
        'query': query,
    })


@login_required
def sent_messages(request):
    """Flat list of messages the user has sent (excluding those they soft-deleted)."""
    query = request.GET.get('q', '')

    messages_qs = (
        Message.objects
        .filter(sender=request.user, deleted_by_sender=False)
        .select_related('sender', 'recipient', 'conversation')
        .order_by('-sent_at')
    )

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query) |
            Q(recipient__username__icontains=query)
        )

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False, deleted_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'sent',
        'unread_count': unread_count,
        'query': query
    })


@login_required
def message_detail(request, pk):
    """Show a message; if it has a conversation, also show the thread — but hide items the user deleted."""
    message = get_object_or_404(
        Message.objects.select_related('conversation', 'sender', 'recipient'),
        pk=pk
    )

    # Must be participant - KR 10/08/2025
    if request.user not in (message.sender, message.recipient):
        return redirect('messages')

    # Don’t allow opening items the current user soft-deleted - KR 10/08/2025
    if (request.user == message.sender and getattr(message, 'deleted_by_sender', False)) or \
       (request.user == message.recipient and getattr(message, 'deleted_by_recipient', False)):
        messages.info(request, "That message was deleted.")
        return redirect('messages')

    # Auto-mark read - KR 10/08/2025
    if message.recipient_id == request.user.id and not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    thread_messages = None
    if message.conversation_id:
        thread_messages = (
            message.conversation.messages
            .filter(
                (Q(sender=request.user) & Q(deleted_by_sender=False)) |
                (Q(recipient=request.user) & Q(deleted_by_recipient=False))
            )
            .select_related('sender', 'recipient')
            .prefetch_related('attachments')
            .order_by('sent_at')
        )

    return render(request, 'messaging/message_detail.html', {
        'message': message,
        'thread_messages': thread_messages,
    })


@login_required
def conversation_detail(request, pk):
    """Jump to the latest visible message in a conversation (reusing message_detail)."""
    convo = get_object_or_404(
        Conversation.objects.prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects
                    .select_related('sender', 'recipient')
                    .filter(
                        (Q(sender=request.user) & Q(deleted_by_sender=False)) |
                        (Q(recipient=request.user) & Q(deleted_by_recipient=False))
                    )
                    .order_by('-sent_at')
            ),
            'participants'
        ),
        pk=pk,
    )

    if not convo.participants.filter(id=request.user.id).exists():
        messages.error(request, "You don't have access to that conversation.")
        return redirect('messages')

    last_msg = next(iter(convo.messages.all()), None)
    if not last_msg:
        messages.info(request, "This conversation has no messages yet.")
        return redirect('messages')

    return redirect('message_detail', pk=last_msg.pk)


@login_required
def compose_message(request):
    """Create a new message; auto‑attach to existing 2‑party thread or create one."""
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                msg = form.save(commit=False)
                msg.sender = request.user

                convo = form.cleaned_data.get('conversation') or _get_or_create_conversation(
                    request.user, form.cleaned_data['recipient']
                )
                msg.conversation = convo
                msg.save()

                files = form.cleaned_data.get('attachments') or []
                for f in files:
                    if not f:
                        continue
                    kwargs = {
                        'message': msg,
                        'file': f,
                        'original_name': getattr(f, 'name', '') or '',
                        'size': getattr(f, 'size', None),
                    }
                    if hasattr(MessageAttachment, 'uploaded_by'):
                        kwargs['uploaded_by'] = request.user
                    MessageAttachment.objects.create(**kwargs)

            messages.success(request, "Message sent.")
            return redirect('messages')
        else:
            messages.error(request, "There was a problem sending your message. Please check the form.")
    else:
        form = MessageForm(user=request.user)

    return render(request, 'messaging/compose.html', {'form': form})


@login_required
def reply_message(request, pk):
    """Reply to a specific message; always stays in the same conversation."""
    original = get_object_or_404(Message, pk=pk)
    if request.user not in (original.sender, original.recipient):
        messages.error(request, "You can't reply to this message.")
        return redirect('messages')

    convo = original.conversation or _get_or_create_conversation(original.sender, original.recipient)
    if not original.conversation_id:
        original.conversation = convo
        original.save(update_fields=['conversation'])

    initial = {
        'recipient': original.sender if request.user == original.recipient else original.recipient,
        'subject': f"Re: {original.subject}",
        'conversation': convo.id,
    }

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                reply = form.save(commit=False)
                reply.sender = request.user
                reply.conversation = convo
                reply.save()

                files = form.cleaned_data.get('attachments') or []
                for f in files:
                    if not f:
                        continue
                    kwargs = {
                        'message': reply,
                        'file': f,
                        'original_name': getattr(f, 'name', '') or '',
                    }
                    if hasattr(MessageAttachment, 'uploaded_by'):
                        kwargs['uploaded_by'] = request.user
                    MessageAttachment.objects.create(**kwargs)

            messages.success(request, "Reply sent.")
            return redirect('messages')
    else:
        form = MessageForm(user=request.user, initial=initial)

    return render(request, 'messaging/compose.html', {
        'form': form,
        'is_reply': True,
        'original_msg': original,
    })

@login_required
def archive_message(request, pk):
    message = get_object_or_404(Message, pk=pk, recipient=request.user)
    message.archived = True
    message.save()
    messages.success(request, "Message archived successfully.")
    return redirect('messages')


@login_required
@require_POST
def delete_message(request, pk):
    """Soft-delete for the current user; hard-delete only when both have deleted."""
    message = get_object_or_404(
        Message,
        Q(pk=pk) & (Q(sender=request.user) | Q(recipient=request.user))
    )
    convo_id = message.conversation_id
    next_url = request.POST.get('next')

    changed = False
    if hasattr(message, 'deleted_by_sender') and request.user == message.sender and not message.deleted_by_sender:
        message.deleted_by_sender = True
        changed = True
    if hasattr(message, 'deleted_by_recipient') and request.user == message.recipient and not message.deleted_by_recipient:
        message.deleted_by_recipient = True
        changed = True

    # If both deleted, remove permanently - KR 11/08/2025
    if getattr(message, 'deleted_by_sender', False) and getattr(message, 'deleted_by_recipient', False):
        message.delete()
        messages.success(request, "Message removed.")
        if next_url:
            return redirect(next_url)
        if convo_id:
            return redirect('conversation_detail', pk=convo_id)
        return redirect('messages')

    if changed:
        message.save(update_fields=['deleted_by_sender', 'deleted_by_recipient'])
    messages.success(request, "Message deleted for you.")

    if next_url:
        return redirect(next_url)
    if convo_id:
        return redirect('conversation_detail', pk=convo_id)
    return redirect('messages')

@login_required
def download_attachment(request, pk):
    a = get_object_or_404(
        MessageAttachment.objects.select_related('message__sender', 'message__recipient'),
        pk=pk
    )
    msg = a.message
    if request.user not in (msg.sender, msg.recipient):
        raise Http404("Not found")

    if not a.file:
        raise Http404("File not available")

    try:
        f = a.file.open("rb")
    except Exception:
        raise Http404("File not available")

    filename = a.original_name or a.file.name
    return FileResponse(f, as_attachment=True, filename=filename)