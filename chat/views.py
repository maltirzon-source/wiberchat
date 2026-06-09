from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q, OuterRef, Subquery, Count
from django.utils import timezone
from django.http import JsonResponse
from accounts.models import Profile
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Message, Statut, PinnedChat, SondageOption

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}! Tu peux maintenant te connecter.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'chat/signup.html', {'form': form})

@login_required
def chat_list(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    user_profile.last_seen = timezone.now()
    user_profile.save()

    pinned_ids = PinnedChat.objects.filter(user=request.user).values_list('pinned_user_id', flat=True)

    last_msg = Message.objects.filter(
        Q(sender=OuterRef('pk'), receiver=request.user) |
        Q(sender=request.user, receiver=OuterRef('pk'))
    ).order_by('-timestamp')

    users = User.objects.exclude(id=request.user.id).annotate(
        last_msg_content=Subquery(last_msg.values('content')[:1]),
        last_msg_time=Subquery(last_msg.values('timestamp')[:1]),
        last_msg_sender_id=Subquery(last_msg.values('sender_id')[:1]),
        last_msg_image=Subquery(last_msg.values('image')[:1]),
        unread_count=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False)
        ),
        is_pinned=Q(id__in=pinned_ids)
    ).filter(
        Q(sent_messages__receiver=request.user) | Q(received_messages__sender=request.user)
    ).distinct().order_by('-is_pinned', '-last_msg_time').select_related('profile')

    return render(request, 'chat/chat_list.html', {
        'users': users,
    })

@login_required
def pin_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    pinned, created = PinnedChat.objects.get_or_create(
        user=request.user,
        pinned_user=other_user
    )
    if not created:
        pinned.delete()
    return redirect('chat_list')

@login_required
def new_chat(request):
    talked_users = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).values_list('sender_id', 'receiver_id')

    talked_ids = set()
    for sender_id, receiver_id in talked_users:
        talked_ids.add(sender_id)
        talked_ids.add(receiver_id)
    talked_ids.discard(request.user.id)

    users = User.objects.exclude(id=request.user.id).exclude(
        id__in=talked_ids
    ).select_related('profile').order_by('username')

    return render(request, 'chat/new_chat.html', {'users': users})

@login_required
def chat_room(request, username):
    other_user = get_object_or_404(User, username=username)

    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True, is_delivered=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')

        if content or image or file:
            new_msg = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content,
                image=image,
                file=file,
                is_delivered=True if getattr(other_user, 'profile', None) and other_user.profile.is_online() else False
            )
            return redirect('chat_room', username=username)

    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    return render(request, 'chat/chat_room.html', {
        'messages': messages_list,
        'other_user': other_user
    })

@csrf_exempt
@login_required
def api_send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receiver = get_object_or_404(User, username=data['receiver'])
            msg = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=data.get('content', ''),
                is_delivered=True if receiver.profile.is_online() else False
            )
            return JsonResponse({'status': 'ok', 'id': msg.id, 'timestamp': msg.timestamp.strftime('%H:%M')})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required
def add_status(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        contenu = request.POST.get('contenu', '')
        if image:
            Statut.objects.create(user=request.user, image=image, contenu=contenu, type='image')
            return JsonResponse({'status': 'ok'})
    return render(request, 'chat/add_status.html')

@login_required
def status_list(request):
    if request.method == 'POST':
        type_status = request.POST.get('type', 'text')
        contenu = request.POST.get('content', '')

        statut = Statut.objects.create(
            user=request.user,
            type=type_status,
            contenu=contenu
        )

        if type_status == 'image' and request.FILES.get('image'):
            statut.image = request.FILES['image']
        elif type_status == 'audio' and request.FILES.get('audio'):
            statut.audio = request.FILES['audio']
        elif type_status == 'poll':
            options = request.POST.getlist('poll_options[]')
            statut.save()
            for opt in options:
                if opt.strip():
                    SondageOption.objects.create(statut=statut, texte=opt.strip())

        statut.save()
        return redirect('status_list')

    # Seulement les status non expirés
    statuts = Statut.objects.filter(date_expire__gt=timezone.now()).select_related('user__profile').prefetch_related('options__votes', 'views')

    # Marquer comme vu
    for s in statuts:
        if request.user not in s.views.all():
            s.views.add(request.user)

    return render(request, 'chat/status_list.html', {'posts': statuts})

@login_required
def vote_sondage(request, option_id):
    option = get_object_or_404(SondageOption, id=option_id)
    # Retire le vote si déjà voté, sinon ajoute
    if request.user in option.votes.all():
        option.votes.remove(request.user)
    else:
        # Retire les autres votes du même sondage
        for opt in option.statut.options.all():
            opt.votes.remove(request.user)
        option.votes.add(request.user)
    return redirect('status_list')

@login_required
def like_statut(request, pk):
    statut = get_object_or_404(Statut, id=pk)
    if statut.likes.filter(id=request.user.id).exists():
        statut.likes.remove(request.user)
    else:
        statut.likes.add(request.user)
    return redirect('status_list')

@login_required
def profile(request):
    # On importe le modèle ici, localement, pour casser la boucle
    from accounts.models import Profile

    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if request.FILES.get('image'):
            user_profile.image = request.FILES['image']
            user_profile.save()
            return HttpResponse(status=200)

    return render(request, 'chat/profile.html', {'profile': user_profile})


@login_required
def delete_statut(request, pk):
    statut = get_object_or_404(Statut, id=pk, user=request.user)
    statut.delete()
    return redirect('status_list')

@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message, id=pk, sender=request.user)
    room_username = message.receiver.username
    message.delete()
    return redirect('chat_room', username=room_username)

@login_required
def delete_conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).delete()
    return redirect('chat_list')