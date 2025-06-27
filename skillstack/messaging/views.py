from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Message
from .forms import MessageForm

@login_required
def inbox(request):
    messages = Message.objects.filter(recipient=request.user)
    return render(request, 'messaging/inbox.html', {'messages': messages})

@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user)
    return render (request, 'messaging/sent.html', {'messages': messages})

@login_required
def message_detail(request, pk):
    message=get_object_or_404(Message, pk=pk, recipient=request.user)
    message.is_read = True
    message.save()
    return render(request, 'messaging/message_detail.html', {'message': message})

@login_required
def compose_message(request):
    if request.method =='POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            return redirect ('inbox')
        
        else:
            form = MessageForm()
        return render(request, 'messaging/compose.html', {'form: form'})