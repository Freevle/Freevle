import random
from django.db.models.signals import post_syncdb
from django.contrib.auth import models
from django.db.utils import IntegrityError
from cygy.settings import DEBUG

def create_groups(sender, **kwargs):
    models.Group(name='Teachers').save()
    models.Group(name='Students').save()

post_syncdb.connect(create_groups, sender=models)

FIRST_NAMES = ('John', 'William', 'Thomas', 'Eric', 'Andrew', 'Raymond', 'Joe',
        'Robert', 'Michael', 'Mark', 'Gary', 'Ash', 'Douglas', 'Samuel',
        'Mary', 'Susan', 'Sarah', 'Amy', 'Laura', 'Betty', 'Catherine',
        'Linda', 'Helen', 'Debra', 'Jean', 'Judith', 'April', 'Lauren',)
SURNAMES = ('Smith', 'Jones', 'Brown', 'Thompson', 'White', 'Scott', 'Coleman',
        'Hughes', 'Butler', 'McDonald', 'Shaw', 'Pond', 'Adams', 'Holmes',)
DOMAINS = ('example', 'random', 'mydomain', 'internetforme', 'generic-isp',)
TLDS = ('.net', '.com', '.org', '.me', '.pro', '.edu',)

def create_user(group, verbosity):
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(SURNAMES)
    username = first_name[0] + last_name
    email = ''.join((first_name, last_name, '@', random.choice(DOMAINS),
        random.choice(TLDS)))

    me = models.User(username=username, first_name=first_name,
            last_name=last_name, email=email, is_staff=True)
    me.set_password('hunter2')
    try:
        me.save()
    except IntegrityError:
        username = username + str(random.randint(0, 99))
        me.username = username
        me.save()
    group.user_set.add(me)

    if verbosity > 1:
        print '- {}: "{} {}" <{}>'.format(username, first_name, last_name, email)

def debug_data(sender, **kwargs):
    verbosity = kwargs['verbosity']
    if verbosity > 1:
        print

    # Create 20 teachers
    print ('Generating 20 random teachers (this may take a while)'
           + (': ' if verbosity > 1 else '.'))

    teachers_group = models.Group.objects.get(name='Teachers') 
    for i in xrange(20):
        create_user(teachers_group, verbosity)
    teachers_group.save()
    if verbosity > 1:
        print

    # Create 100 students
    print ('Generating 100 random students (this may take a while)'
            + (': ' if verbosity > 1 else '.'))

    students_group = models.Group.objects.get(name='Students') 
    for i in xrange(100):
        create_user(students_group, verbosity)
    students_group.save()
    if verbosity > 1:
        print

if DEBUG:
    post_syncdb.connect(debug_data, sender=models)
