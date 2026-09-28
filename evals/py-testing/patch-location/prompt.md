---
name: "py-testing: corrects patch location mistake"
tags: ["py-testing", "mocking"]
runs: 3
max_turns: 6
---

My mock isn't working. The real function is still being called even though I patched it. Here's my code:

```python
# myapp/notifications.py
from myapp.email import send_email

def notify_user(user):
    send_email(user.email)
```

```python
# tests/test_notifications.py
from unittest.mock import patch

@patch('myapp.email.send_email')
def test_notify_user(mock_send):
    notify_user({'email': 'test@example.com'})
    assert mock_send.called  # fails, why?
```
