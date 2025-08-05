from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Message
from .forms import MessageForm

@login_required
def inbox(request):
    query = request.GET.get('q', '')
    messages_qs = Message.objects.filter(recipient=request.user)

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) | Q(sender__username__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'messaging/inbox.html', {
        'messages': messages_qs,
        'active_tab': 'inbox',
        'unread_count': unread_count,
        'query': query
    })


@login_required
def sent_messages(request):
    query = request.GET.get('q', '')
    messages_qs = Message.objects.filter(sender=request.user)

    if query:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=query) | Q(recipient__username__icontains=query)
        )

    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'messaging/inbox.html', {
        'messages': messages_qs,
        'active_tab': 'sent',
        'unread_count': unread_count,
        'query': query
    })

@login_required
def message_detail(request, pk):
    message=get_object_or_404(Message, pk=pk, recipient=request.user)
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
            return redirect ('inbox')
    else:
        form = MessageForm(user=request.user)
        
    return render(request, 'messaging/compose.html', {'form': form})