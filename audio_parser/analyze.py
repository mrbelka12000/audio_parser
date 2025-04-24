from openai import OpenAI
import config

client = OpenAI(
    # This is the default and can be omitted
    api_key=config.ai_token,
)
def get_analytics_from_ai(transcript):
    
    # Пример запроса
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": 'Я предоставлю тебе транскрипт или краткое содержание нашей ежедневной встречи. Твоя задача — проанализировать его и составить чёткий, действенный план. Результат должен включать: 	1.	Ключевые обсуждаемые темы 	2.	Задачи к выполнению (с ответственными и сроками, если есть) 	3.	Открытые вопросы или блокеры 	4.	Следующие шаги  Будь кратким и используй маркированные списки для наглядности.'},
            {
                "role": "user",
                "content": transcript,
            },
        ],
    )


    return completion.choices[0].message.content