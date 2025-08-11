from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Q, Prefetch
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, Http404
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from .models import Message, Conversation, MessageAttachment
from .forms import MessageForm

# --- Utility for unread count ---
@login_required
def api_unread_count(request):
    count = Message.objects.filter(
        recipient=request.user, is_read=False,
        deleted_by_recipient=False, archived_by_recipient=False
    ).count()
    return JsonResponse({"unread": count})

# --- API for fetching latest messages ---
@login_required
def api_inbox_latest(request):
    qs = Message.objects.filter(
        (Q(sender=request.user) & Q(deleted_by_sender=False) & Q(archived_by_sender=False)) |
        (Q(recipient=request.user) & Q(deleted_by_recipient=False) & Q(archived_by_recipient=False))
    ).select_related('sender', 'recipient').order_by('-sent_at')

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

# --- API mark read ---
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


# --- Conversation utilities ---
def _get_or_create_conversation(user_a, user_b):
    convo = Conversation.objects.filter(participants=user_a).filter(participants=user_b).first()
    if not convo:
        convo = Conversation.objects.create()
        convo.participants.add(user_a, user_b)
    return convo

# --- Archive / Unarchive message ---
@login_required
@require_POST
def archive_message(request, pk):
    m = get_object_or_404(Message, pk=pk, sender=request.user) if request.user == Message.objects.filter(pk=pk).first().sender else get_object_or_404(Message, pk=pk, recipient=request.user)
    if request.user == m.sender and not m.archived_by_sender:
        m.archived_by_sender = True
        m.save(update_fields=['archived_by_sender'])
    elif request.user == m.recipient and not m.archived_by_recipient:
        m.archived_by_recipient = True
        m.save(update_fields=['archived_by_recipient'])

    messages.success(request, "Message archived.")
    return redirect(request.POST.get('next') or 'messages')

@login_required
@require_POST
def unarchive_message(request, pk):
    m = get_object_or_404(Message, pk=pk, sender=request.user) if request.user == Message.objects.filter(pk=pk).first().sender else get_object_or_404(Message, pk=pk, recipient=request.user)
    if request.user == m.sender and m.archived_by_sender:
        m.archived_by_sender = False
        m.save(update_fields=['archived_by_sender'])
    elif request.user == m.recipient and m.archived_by_recipient:
        m.archived_by_recipient = False
        m.save(update_fields=['archived_by_recipient'])

    messages.success(request, "Message unarchived.")
    return redirect(request.POST.get('next') or 'archived_messages')

# --- Views with archived filtering ---
@login_required
def inbox(request):
    conversations = Conversation.objects.filter(participants=request.user).prefetch_related(
        Prefetch(
            'messages',
            queryset=Message.objects.select_related('sender', 'recipient')
                .filter(
                    (Q(sender=request.user) & Q(deleted_by_sender=False) & Q(archived_by_sender=False)) |
                    (Q(recipient=request.user) & Q(deleted_by_recipient=False) & Q(archived_by_recipient=False))
                )
                .order_by('-sent_at')
        ),
        'participants',
    )

    latest_messages = [next(iter(convo.messages.all()), None) for convo in conversations]
    latest_messages = [m for m in latest_messages if m]

    query = request.GET.get('q', '').strip()
    if query:
        query_lower = query.lower()
        latest_messages = [
            m for m in latest_messages
            if (query_lower in (m.subject or '').lower()) or
               (query_lower in (m.body or '').lower()) or
               any(query_lower in (p.get_full_name() or p.username).lower() for p in m.conversation.participants.all())
        ]
    latest_messages.sort(key=lambda m: m.sent_at, reverse=True)

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False,
        deleted_by_recipient=False, archived_by_recipient=False
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
    messages_qs = Message.objects.filter(
        (Q(sender=request.user) & Q(deleted_by_sender=False) & Q(archived_by_sender=False)) |
        (Q(recipient=request.user) & Q(deleted_by_recipient=False) & Q(archived_by_recipient=False))
    ).select_related('sender', 'recipient', 'conversation').order_by('-sent_at')

    query = request.GET.get('q', '').strip()
    if query:
        messages_qs = messages_qs.filter(Q(subject__icontains=query) | Q(body__icontains=query))

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False,
        deleted_by_recipient=False, archived_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'all',
        'unread_count': unread_count,
        'query': query,
    })

@login_required
def sent_messages(request):
    messages_qs = Message.objects.filter(
        sender=request.user, deleted_by_sender=False, archived_by_sender=False
    ).select_related('sender', 'recipient', 'conversation').order_by('-sent_at')

    query = request.GET.get('q', '').strip()
    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query) |
            Q(recipient__username__icontains=query)
        )

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False,
        deleted_by_recipient=False, archived_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'sent',
        'unread_count': unread_count,
        'query': query,
    })

@login_required
def archived_messages(request):
    messages_qs = Message.objects.filter(
        Q(sender=request.user, archived_by_sender=True, deleted_by_sender=False) |
        Q(recipient=request.user, archived_by_recipient=True, deleted_by_recipient=False)
    ).select_related('sender', 'recipient', 'conversation').order_by('-sent_at')

    query = request.GET.get('q', '').strip()
    if query:
        messages_qs = messages_qs.filter(Q(subject__icontains=query) | Q(body__icontains=query))

    unread_count = Message.objects.filter(
        recipient=request.user, is_read=False,
        deleted_by_recipient=False, archived_by_recipient=False
    ).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'archived',
        'unread_count': unread_count,
        'query': query,
    })

@login_required
def message_detail(request, pk):
    message = get_object_or_404(
        Message.objects.select_related('conversation', 'sender', 'recipient'),
        pk=pk
    )

    if request.user not in (message.sender, message.recipient):
        return redirect('messages')

    # Hide deleted
    if (request.user == message.sender and message.deleted_by_sender) or (
        request.user == message.recipient and message.deleted_by_recipient
    ):
        messages.info(request, "That message was deleted.")
        return redirect('messages')

    # Hide archived
    if (request.user == message.sender and message.archived_by_sender) or (
        request.user == message.recipient and message.archived_by_recipient
    ):
        messages.info(request, "This message is archived.")
        return redirect('archived_messages')

    if request.user == message.recipient and not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    thread_messages = None
    if message.conversation_id:
        thread_messages = message.conversation.messages.filter(
            (Q(sender=request.user) & Q(deleted_by_sender=False) & Q(archived_by_sender=False)) |
            (Q(recipient=request.user) & Q(deleted_by_recipient=False) & Q(archived_by_recipient=False))
        ).select_related('sender', 'recipient').order_by('sent_at')

    return render(request, 'messaging/message_detail.html', {
        'message': message,
        'thread_messages': thread_messages,
    })

@login_required
def conversation_detail(request, pk):
    convo = get_object_or_404(Conversation.objects.prefetch_related(
        Prefetch(
            'messages',
            queryset=Message.objects.select_related('sender', 'recipient')
                .filter(
                    (Q(sender=request.user) & Q(deleted_by_sender=False) & Q(archived_by_sender=False)) |
                    (Q(recipient=request.user) & Q(deleted_by_recipient=False) & Q(archived_by_recipient=False))
                ).order_by('-sent_at')
        ),
        'participants'
    ), pk=pk)

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
                    if not f: continue
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
                    if not f: continue
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
@require_POST
def delete_message(request, pk):
    """Soft-delete for current user; hard-delete only if both have deleted."""
    message = get_object_or_404(
        Message,
        Q(pk=pk) & (Q(sender=request.user) | Q(recipient=request.user))
    )
    convo_id = message.conversation_id
    next_url = request.POST.get('next')
    changed = False

    if request.user == message.sender and not message.deleted_by_sender:
        message.deleted_by_sender = True
        changed = True
    if request.user == message.recipient and not message.deleted_by_recipient:
        message.deleted_by_recipient = True
        changed = True

    if message.deleted_by_sender and message.deleted_by_recipient:
        message.delete()
        messages.success(request, "Message removed.")
        return redirect(next_url or ('conversation_detail' if convo_id else 'messages'))

    if changed:
        message.save(update_fields=['deleted_by_sender', 'deleted_by_recipient'])
    messages.success(request, "Message deleted for you.")

    return redirect(next_url or ('conversation_detail', convo_id) if convo_id else 'messages')

@login_required
def download_attachment(request, pk):
    a = get_object_or_404(MessageAttachment.objects.select_related('message__sender', 'message__recipient'), pk=pk)
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