from lib.database import Goal # type: ignore

goals = [
    Goal(
        id=0,
        name='SQL Injection',
        description='View the "private" profiles which are not normally visible',
        points=20
    ),
    Goal(
        id=1,
        name='SQL UNION Attack',
        description='Find out what Alice\'s balance is',
        points=20
    ),
    Goal(
        id=2,
        name='Client-side security',
        description='Send a transaction which steals money from another user',
        points=20
    ),
    Goal(
        id=3,
        name='CSRF',
        description='Create a local HTML file which exploits CSRF to send you a transaction',
        points=20
    ),
    Goal(
        id=4,
        name='Stored XSS',
        description='Trick the support staff into sending you money',
        points=20
    ),
]