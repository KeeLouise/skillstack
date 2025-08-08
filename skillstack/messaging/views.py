from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Message
from .forms import MessageForm

@login_required
def inbox(request):
    query = request.GET.get('q', '')
    messages_qs = Message.objects.filter(recipient=request.user).order_by('-sent_at')

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(sender__first_name__icontains=query) |
            Q(sender__last_name__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'inbox',
        'unread_count': unread_count,
        'query': query
    })

@login_required
def sent_messages(request):
    query = request.GET.get('q', '')
    messages_qs = Message.objects.filter(sender=request.user).order_by('-sent_at')

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'sent',
        'unread_count': unread_count,
        'query': query
    })

@login_required
def all_messages(request):
    query = request.GET.get('q', '')
    messages_qs = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) |
            Q(body__icontains=query) |
            Q(sender__first_name__icontains=query) |
            Q(sender__last_name__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'messaging/messages.html', {
        'messages': messages_qs,
        'active_tab': 'all',
        'unread_count': unread_count,
        'query': query
    })

@login_required
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)

    if request.user != message.recipient and request.user != message.sender:
        return redirect('messages')

    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()

    return render(request, 'messaging/message_detail.html', {'message': message})

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            return redirect('messages')
    else:
        form = MessageForm(user=request.user)
        
    return render(request, 'messaging/compose.html', {'form': form})

@login_required
def reply_message(request, pk):
    original_msg = get_object_or_404(Message, pk=pk)

    initial_data = {
        'recipient': original_msg.sender,
        'subject': f"Re: {original_msg.subject}",
    }

    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.save()
            return redirect('messages')
    else:
        form = MessageForm(user=request.user, initial=initial_data)

    return render(request, 'messaging/compose.html', {
        'form': form,
        'is_reply': True,
        'original_msg': original_msg
    })

@login_required
@require_POST
def delete_message(request, pk):
    message = get_object_or_404(
        Message,
        Q(pk=pk) & (Q(sender=request.user) | Q(recipient=request.user))
    )

    message.delete()
    django_messages.success(request, "Message deleted successfully.")
    return redirect('messages')