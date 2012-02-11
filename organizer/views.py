# Create your views here.

import datetime

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.template.response import TemplateResponse
from django.views.generic.detail import DetailView
from django.views.generic.dates import YearMixin, MonthMixin, DayMixin, DateMixin
from django.views.generic.base import View

from django.contrib.auth.models import User

class UserView(View, YearMixin, MonthMixin, DayMixin):

    '''
    lesson_set1 = queryset
    lesson_set2 = queryset
    lesson_set3 = queryset
    > announcements = queryset
    > comming_homework = queryset
    > day_names = date.strftime('%a')
    > lesson_sets = [lesson_set1, lesson_set2, lesson_set3]
    
    To write:
    get_comming_homework()
    get_anouncements()
    get_day_names()
    get_lesson_set_dict()
    get_lesson_set()
    get_date()
    
    UITVAL?!
    LEGENDA!
    
    '''
    username_url_kwarg = 'username'
    announcements = None
    comming_homework = None
    day_names = None
    number_future_days = 2

    def get_date(self):
        pass

    def get_announcements(self, date):
        pass

    def get_day_names(self, date):
        pass

    def get_comming_homework(self, date):
        pass

    def get_lesson_set(self, date):
        pass

    # Homemade
    lesson_set_dict = None
    def get_lesson_set_dict(self, date):
        """
        Get the list of lessonsets. This is a list of querysets.
        """
        if self.lesson_set_dict is not None:
            lesson_set_dict = self.lesson_set_dict
        else:
            username = self.kwargs.get(self.username_url_kwarg, None)
            
            if username is not None:
                try:
                    user = User.objects.all().get(username=username)
                except ObjectDoesNotExist:
                    raise Http404
            else:
                raise ImproperlyConfigured("UserView needs to be called with "
                                           "a username")
            
            lesson_set_dict = [self.get_lesson_set(date + timedelta(days=n))
                               for n in range(self.number_future_days)]
            
        return lesson_set_dict


    def get_queryset(self):   ## << Here
        """
        Get the list of items for this view. This must be an interable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        if self.queryset is not None:
            queryset = self.queryset
            if hasattr(queryset, '_clone'):
                queryset = queryset._clone()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(u"'%s' must define 'queryset' or 'model'"
                                       % self.__class__.__name__)
        return queryset


    # -- Done --
    ## Original    
    def get_template_names(self):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        if self.template_name is None:
            raise ImproperlyConfigured(
                "TemplateResponseMixin requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return [self.template_name]
    
    ## Original
    template_name = None
    response_class = TemplateResponse
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context.
        """
        return self.response_class(
            request = self.request,
            template = self.get_template_names(),
            context = context,
            **response_kwargs
        )

    ## Edited
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    ## Edited
    def get_context_data(self):
        """
        Get the context for this view.
        """
        date = self.get_date()
        announcements = self.get_announcements(date)
        comming_homework = self.get_comming_homework(date)
        day_names = self.get_day_names(date)
        lesson_set_dict = self.get_lesson_set_dict(date)

        context = {
            'announcements': announcements,
            'comming_homework': comming_homework,
            'day_names': day_names,
            'lesson_set_dict': lesson_set_dict,
        }

        return context




# I'm just leaving this here for now if I want to use parts later
def _get_next_prev_month(generic_view, naive_result, is_previous, use_day_names):
    """
    Helper: Get the next or the previous valid date. The idea is to allow
    links on month/day views to never be 404s by never providing a date
    that'll be invalid for the given view.

    This is a bit complicated since it handles both next and previous months
    and days (for MonthArchiveView and DayArchiveView); hence the coupling to generic_view.

    However in essence the logic comes down to:

        * If allow_empty and allow_future are both true, this is easy: just
          return the naive result (just the next/previous day or month,
          reguardless of object existence.)

        * If allow_empty is true, allow_future is false, and the naive month
          isn't in the future, then return it; otherwise return None.

        * If allow_empty is false and allow_future is true, return the next
          date *that contains a valid object*, even if it's in the future. If
          there are no next objects, return None.

        * If allow_empty is false and allow_future is false, return the next
          date that contains a valid object. If that date is in the future, or
          if there are no next objects, return None.

    """
    date_field = generic_view.get_date_field()
    allow_empty = generic_view.get_allow_empty()
    allow_future = generic_view.get_allow_future()

    # If allow_empty is True the naive value will be valid
    if allow_empty:
        result = naive_result

    # Otherwise, we'll need to go to the database to look for an object
    # whose date_field is at least (greater than/less than) the given
    # naive result
    else:
        # Construct a lookup and an ordering depending on whether we're doing
        # a previous date or a next date lookup.
        if is_previous:
            lookup = {'%s__lte' % date_field: naive_result}
            ordering = '-%s' % date_field
        else:
            lookup = {'%s__gte' % date_field: naive_result}
            ordering = date_field

        qs = generic_view.get_queryset().filter(**lookup).order_by(ordering)

        # Snag the first object from the queryset; if it doesn't exist that
        # means there's no next/previous link available.
        try:
            result = getattr(qs[0], date_field)
        except IndexError:
            result = None

    # Convert datetimes to a dates
    if hasattr(result, 'date'):
        result = result.date()

    # For month views, we always want to have a date that's the first of the
    # month for consistency's sake.
    if result and use_day_names:
        result = result.replace(day=1)

    # Check against future dates.
    if result and (allow_future or result < datetime.date.today()):
        return result
    else:
        return None






class UserDetailView(DetailView):
    username_field = 'username'
    username_url_kwarg = 'username'

    def get_object(self, queryset=None):
        

        # Use a custom queryset if provided
        if queryset is None:
            queryset = self.get_queryset()

        username = self.kwargs.get(self.username_url_kwarg, None)

        # Try looking up by username.
        if username is not None:
            username_field = self.username_field
            queryset = queryset.filter(**{username_field: username})

        # If none of those are defined, it's an error.
        else:
            raise AttributeError(u'Generic detail view {} must be called with '
                                 u'a username.'.format(self.__class__.__name__))

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(
                _(u'No {verbose_name} found matching the query').format(
                    verbose_name=queryset.model._meta.verbose_name
                    )
                )
        return obj
