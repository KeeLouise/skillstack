from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, Prefetch

from .models import Message, Conversation, MessageAttachment
from .forms import MessageForm


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
    """Show one card per conversation (latest message), ordered by last activity."""
    query = request.GET.get('q', '')

    conversations = (
        Conversation.objects.filter(participants=request.user)
        .annotate(last_sent=Max('messages__sent_at'))
        .order_by('-last_sent')
        .prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender', 'recipient').order_by('-sent_at')
            ),
            'participants',
        )
    )

    if query:
        conversations = conversations.filter(
            Q(messages__subject__icontains=query) |
            Q(messages__body__icontains=query) |
            Q(participants__first_name__icontains=query) |
            Q(participants__last_name__icontains=query) |
            Q(participants__username__icontains=query)
        ).distinct()

    latest_messages = []
    for convo in conversations:
        last_msg = next(iter(convo.messages.all()), None)
        if last_msg:
            latest_messages.append(last_msg)

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(
        request,
        'messaging/messages.html',
        {
            'conversations': conversations,
            'messages': latest_messages,      
            'message_list': latest_messages,  
            'active_tab': 'inbox',
            'unread_count': unread_count,
            'query': query,
        }
    )


@login_required
def all_messages(request):
    """Flat list of all messages to/from the user."""
    query = request.GET.get('q', '')

    messages_qs = (
        Message.objects
        .filter(Q(sender=request.user) | Q(recipient=request.user))
        .select_related('sender', 'recipient', 'conversation')
        .order_by('-sent_at')
    )

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) | Q(body__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(
        request,
        'messaging/messages.html',
        {
            'messages': messages_qs,
            'message_list': messages_qs,
            'active_tab': 'all',
            'unread_count': unread_count,
            'query': query,
        }
    )


@login_required
def sent_messages(request):
    """Flat list of messages the user has sent."""
    query = request.GET.get('q', '')
    messages_qs = (
        Message.objects
        .filter(sender=request.user)
        .select_related('recipient', 'conversation')
        .order_by('-sent_at')
    )

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query) |
            Q(recipient__username__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(
        request,
        'messaging/messages.html',
        {
            'messages': messages_qs,
            'message_list': messages_qs,
            'active_tab': 'sent',
            'unread_count': unread_count,
            'query': query
        }
    )


@login_required
def message_detail(request, pk):
    """Show a message; if it has a conversation, also show the thread."""
    message = (
        Message.objects
        .select_related('conversation', 'sender', 'recipient')
        .get(pk=pk)
    )

    if request.user not in (message.sender, message.recipient):
        return redirect('messages')

    if message.recipient_id == request.user.id and not message.is_read:
        message.is_read = True
        message.save(update_fields=['is_read'])

    thread_messages = None
    if message.conversation_id:
        thread_messages = (
            message.conversation.messages
            .select_related('sender', 'recipient')
            .prefetch_related('attachments')
            .order_by('sent_at')
        )

    return render(
        request,
        'messaging/message_detail.html',
        {
            'message': message,
            'thread_messages': thread_messages,
        }
    )


@login_required
def conversation_detail(request, pk):
    """Jump to the latest message in a conversation (and reuse message_detail)."""
    convo = get_object_or_404(
        Conversation.objects.prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender', 'recipient').order_by('-sent_at')
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


def compose_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user

            convo = form.cleaned_data.get('conversation')
            if not convo:
                convo = _get_or_create_conversation(request.user, form.cleaned_data['recipient'])
            msg.conversation = convo
            msg.save()

            for f in request.FILES.getlist('attachments'):
                MessageAttachment.objects.create(
                    message=msg,
                    file=f,
                    uploaded_by=getattr(request.user, "pk", None) and request.user,
                    original_name=getattr(f, 'name', '')
                )

            messages.success(request, "Message sent.")
            return redirect('messages')
    else:
        form = MessageForm(user=request.user)

    return render(request, 'messaging/compose.html', {'form': form})


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
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.conversation = convo
            reply.save()

            for f in request.FILES.getlist('attachments'):
                MessageAttachment.objects.create(
                    message=reply,
                    file=f,
                    uploaded_by=getattr(request.user, "pk", None) and request.user,
                    original_name=getattr(f, 'name', '')
                )

            messages.success(request, "Reply sent.")
            return redirect('messages')
    else:
        form = MessageForm(user=request.user, initial=initial)

    return render(request, 'messaging/compose.html', {'form': form, 'is_reply': True, 'original_msg': original})


@login_required
@require_POST
def delete_message(request, pk):
    """Allow sender or recipient to delete a message."""
    message = get_object_or_404(
        Message,
        Q(pk=pk) & (Q(sender=request.user) | Q(recipient=request.user))
    )
    message.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect('messages')