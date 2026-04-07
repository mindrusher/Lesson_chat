from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import InteractionRecord
from .question_bank import questions
import json
import requests
from celery import shared_task
from django.core.cache import cache


def chat_view(request):
    """
        Главная страница чата
    """
    return render(request, 'chat.html', {'questions_count': len(questions)})


@csrf_exempt
@require_http_methods(["POST"])
def start_lesson(request):
    """
        Начинает урок, создаёт первую сессию
    """
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    InteractionRecord.objects.filter(session_id=session_id).delete()

    first_question = questions[0]
    record = InteractionRecord.objects.create(
        session_id=session_id,
        question=first_question['question'],
        correct_answer=first_question['correct_answer'],
        question_order=0,
        status='pending'
    )
    
    return JsonResponse({
        'success': True,
        'session_id': session_id,
        'question': first_question['question'],
        'question_number': 1,
        'total_questions': len(questions)
    })


@csrf_exempt
@require_http_methods(["POST"])
def submit_answer(request):
    """
        Принимает ответ пользователя
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_answer = data.get('answer', '')
        question_order = data.get('question_order', 0)
        
        record = InteractionRecord.objects.get(
            session_id=session_id,
            question_order=question_order,
            status='pending'
        )
        
        record.user_answer = user_answer
        record.answered_at = timezone.now()
        record.status = 'processing'
        record.save()
        
        check_answer_task.delay(record.id)
        
        next_order = question_order + 1
        if next_order < len(questions):
            next_question = questions[next_order]
            next_record = InteractionRecord.objects.create(
                session_id=session_id,
                question=next_question['question'],
                correct_answer=next_question['correct_answer'],
                question_order=next_order,
                status='pending'
            )
            next_question_text = next_question['question']
            is_last = False
        else:
            next_question_text = None
            is_last = True
        
        return JsonResponse({
            'success': True,
            'next_question': next_question_text,
            'next_question_number': next_order + 1 if next_question_text else None,
            'is_last': is_last
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@shared_task
def check_answer_task(record_id):
    """
        Celery задача для проверки ответа через ML сервис
    """
    import time
    from django.utils import timezone
    
    try:
        record = InteractionRecord.objects.get(id=record_id)
        
        time.sleep(5)  # Имитация задержки
        
        try:
            response = requests.post(
                'http://ml_service:8001/check_answer',
                json={
                    'question': record.question,
                    'correct_answer': record.correct_answer,
                    'user_answer': record.user_answer or ''
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                record.is_correct = bool(result.get('is_correct', 0))
                record.status = 'checked'
            else:
                record.status = 'error'
                record.error_message = f'ML сервис вернул код {response.status_code}'
                
        except requests.exceptions.RequestException as e:
            record.status = 'error'
            record.error_message = str(e)
        
        record.checked_at = timezone.now()
        record.save()

        cache.set(f'answer_result_{record_id}', {
            'is_correct': record.is_correct,
            'status': record.status
        }, timeout=300)
        
    except Exception as e:
        print(f"Error in check_answer_task: {e}")
