# API contract (черновик)

Согласовать и зафиксировать до интеграции.

## Планируемый endpoint
`POST /api/v1/recommendations`

Пример входных данных:
```json
{
  "user": {
    "stage": "early",
    "industry": "retail",
    "current_goal": "marketing",
    "experience": "beginner"
  },
  "history": []
}
```

Пример ответа:
```json
{
  "recommendations": [
    {
      "material_id": "demo-001",
      "title": "Название материала",
      "score": 0.91,
      "reason": "Соответствует текущей задаче пользователя",
      "next_step": "Открыть материал"
    }
  ]
}
```

Это контракт-заготовка. Поля необходимо сверить с реальной выгрузкой и согласовать всей командой.
