# Сheck Your Code Against the Following Points

## Don"t Push db files

Make sure you don"t push db files (files with `.sqlite`, `.db3`, etc. extension).

## Code Efficiency
Don"t split the date, it"s already in the format needed.

Good example:

```python
queryset = queryset.filter(show_time=date)
```

Bad example:

```python
date = date.split("-")
queryset = queryset.filter(show_time__year=date[0], 
                           show_time__month=date[1], 
                           show_time__day=date[2])
```

## Code Style
1. Make sure you"ve added a blank line at the end to all your files.
2. Group imports using `()` if needed.

Good example:

```python
from django.contrib.auth.mixins import (
    LoginRequiredMixin, 
    UserPassesTestMixin, 
    PermissionRequiredMixin,
)
```

Bad example:

```python
from django.contrib.auth.mixins import LoginRequiredMixin, \
    UserPassesTestMixin, PermissionRequiredMixin
```

Another bad example:

```python
from django.contrib.auth.mixins import (
    LoginRequiredMixin, 
    UserPassesTestMixin, PermissionRequiredMixin,
)
```

## Clean Code

Add comments, prints, and functions to check your solution when you write your code. 
Don"t forget to delete them when you are ready to commit and push your code.
