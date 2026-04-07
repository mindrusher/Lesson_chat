import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';

export default function Home() {
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [messages, setMessages] = useState([]);
  const [answer, setAnswer] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLessonActive, setIsLessonActive] = useState(false);
  const [status, setStatus] = useState('Готов к работе');
  const timerRef = useRef(null);
  const messagesEndRef = useRef(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Добавляем Bootstrap CSS
    const link = document.createElement('link');
    link.href = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (text, isQuestion) => {
    setMessages(prev => [...prev, { text, isQuestion, timestamp: new Date() }]);
  };

  const startTimer = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      if (isLoading || !isLessonActive) return;
      handleTimeout();
    }, 30000);
  };

  const handleTimeout = async () => {
    if (!currentQuestion || isLoading) return;
    
    setStatus('Время вышло! Отправляем пустой ответ...');
    addMessage('⏰ Время на ответ истекло', false);
    
    try {
      const response = await fetch(`${API_URL}/api/submit-answer/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answer: '',
          question_order: questionNumber - 1
        })
      });
      
      const data = await response.json();
      if (data.next_question) {
        setTimeout(() => {
          setCurrentQuestion(data.next_question);
          setQuestionNumber(data.next_question_number);
          addMessage(data.next_question, true);
          setIsLoading(false);
          setStatus('Ожидаем ответ...');
          startTimer();
        }, 2000);
      } else if (data.is_last) {
        setStatus('Урок завершен! 🎉');
        setIsLessonActive(false);
        addMessage('🎉 Поздравляем! Урок завершен!', false);
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus('Ошибка при отправке');
      setIsLoading(false);
    }
  };

  const startLesson = async () => {
    setIsLoading(true);
    setStatus('Начинаем урок...');
    
    try {
      const response = await fetch(`${API_URL}/api/start-lesson/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      const data = await response.json();
      if (data.success) {
        setSessionId(data.session_id);
        setCurrentQuestion(data.question);
        setQuestionNumber(data.question_number);
        setMessages([]);
        addMessage(data.question, true);
        setIsLessonActive(true);
        setIsLoading(false);
        setStatus('Ожидаем ответ...');
        startTimer();
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus('Ошибка при начале урока');
      setIsLoading(false);
    }
  };

  const sendAnswer = async () => {
    if (!answer.trim() || isLoading || !isLessonActive) return;
    
    clearTimeout(timerRef.current);
    setIsLoading(true);
    const userAnswer = answer;
    addMessage(userAnswer, false);
    setAnswer('');
    setStatus('Отправляем на проверку...');
    
    try {
      const response = await fetch(`${API_URL}/api/submit-answer/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answer: userAnswer,
          question_order: questionNumber - 1
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setStatus('Проверяем ответ (5-8 секунд)... ⏳');
        
        // Ждем результата проверки
        setTimeout(() => {
          if (data.next_question) {
            setCurrentQuestion(data.next_question);
            setQuestionNumber(data.next_question_number);
            addMessage(data.next_question, true);
            setIsLoading(false);
            setStatus('Ожидаем ответ...');
            startTimer();
          } else if (data.is_last) {
            setStatus('Урок завершен! 🎉');
            setIsLessonActive(false);
            addMessage('🎉 Урок завершен! Спасибо за участие!', false);
            setIsLoading(false);
          }
        }, 6000);
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus('Ошибка при отправке');
      setIsLoading(false);
      startTimer();
    }
  };

  return (
    <>
      <Head>
        <title>Образовательный чат - Урок программирования</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      
      <div className="container mt-5">
        <div className="row justify-content-center">
          <div className="col-md-8">
            <div className="card shadow">
              <div className="card-header bg-primary text-white">
                <h3 className="mb-0">📚 Урок программирования</h3>
                <small>Интерактивное обучение с проверкой ответов</small>
              </div>
              
              <div className="card-body" style={{ height: '500px', overflowY: 'auto', background: '#f8f9fa' }}>
                {messages.length === 0 ? (
                  <div className="text-center text-muted mt-5">
                    <p>👋 Добро пожаловать на урок!</p>
                    <p>Нажмите "Начать урок" чтобы начать обучение</p>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div key={idx} className={`mb-3 ${msg.isQuestion ? 'text-start' : 'text-end'}`}>
                      <div className={`d-inline-block p-3 rounded ${msg.isQuestion ? 'bg-light border' : 'bg-primary text-white'}`}>
                        {msg.text}
                      </div>
                      <div className="small text-muted mt-1">
                        {msg.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="card-footer">
                {!isLessonActive ? (
                  <button 
                    className="btn btn-success w-100" 
                    onClick={startLesson} 
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Загрузка...
                      </>
                    ) : (
                      '🚀 Начать урок'
                    )}
                  </button>
                ) : (
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendAnswer()}
                      placeholder="Введите ваш ответ..."
                      disabled={isLoading}
                      autoFocus
                    />
                    <button 
                      className="btn btn-primary" 
                      onClick={sendAnswer} 
                      disabled={isLoading || !answer.trim()}
                    >
                      {isLoading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          Отправка...
                        </>
                      ) : (
                        '📤 Отправить'
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            <div className="mt-3 text-center">
              <div className="badge bg-secondary p-2">
                {isLoading && <span className="spinner-border spinner-border-sm me-2"></span>}
                {status}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}